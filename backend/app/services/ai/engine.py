"""AI engine orchestration.

The four public entrypoints required by the brief:
  * generate_asset_deep_dive
  * analyze_portfolio
  * generate_signal
  * generate_report

Each follows the same shape — and this shape IS the product:

    1. OBSERVED : pull raw facts (prices, fundamentals) with source + as_of.
    2. DERIVED  : compute metrics in the deterministic quant core.
    3. NARRATIVE: retrieve evidence (RAG) + ask the LLM to explain ONLY the
                  observed facts and derived metrics, citing each.
    4. GUARDRAIL: assemble the 3-layer Envelope, run compliance, write audit.

Nothing here mutates raw data. The LLM never does arithmetic on raw facts.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.logging import get_logger
from app.models import Asset, Portfolio
from app.repository import repo
from app.schemas.envelope import Derived, Envelope, Narrative, Observed
from app.services.ai.agents import AgentContext, ResearchAgent
from app.services.ai.guardrails import GuardrailContext, apply
from app.services.ai.llm import get_llm
from app.services.ai.rag import retriever
from app.services.risk import analytics

log = get_logger(__name__)


# --- helpers ---------------------------------------------------------------
def _factor_scores_for(asset: Asset) -> dict[str, float]:
    """STUB: derive per-asset factor scores. Real impl reads the feature store."""
    seed = sum(ord(c) for c in asset.symbol)
    return {
        "value": round(((seed % 7) - 3) / 3, 3),
        "growth": round(((seed % 5) - 2) / 2, 3),
        "momentum": round(((seed % 11) - 5) / 5, 3),
        "quality": round(((seed % 4) - 1) / 3, 3),
        "size": round(((seed % 9) - 4) / 4, 3),
        "volatility": round(((seed % 6) - 3) / 3, 3),
    }


def _observed_price(asset: Asset) -> Observed | None:
    bars = repo.latest_prices(asset.id, limit=1)
    if not bars:
        return None
    bar = bars[-1]
    return Observed(
        field=f"price.close.{asset.symbol}",
        value=bar.close,
        source=bar.source,
        as_of=bar.ts,
        unit=asset.currency,
    )


# --- 1. asset deep-dive -----------------------------------------------------
def generate_asset_deep_dive(*, asset: Asset, gctx: GuardrailContext, sections: list[str] | None = None) -> Envelope:
    llm = get_llm()
    actx = AgentContext(language=gctx.language)
    env = Envelope(language=gctx.language)

    # 1. OBSERVED
    price = _observed_price(asset)
    if price:
        env.observed.append(price)
    snap = repo.latest_fundamental(asset.id)
    if snap:
        for k, v in snap.ratios.items():
            env.observed.append(
                Observed(
                    field=f"fundamental.{k}.{asset.symbol}",
                    value=v,
                    source=snap.source,
                    as_of=snap.as_of,
                )
            )

    # 2. DERIVED — factor scores for this asset (methodology exposed)
    factor = _factor_scores_for(asset)
    env.derived.append(
        Derived(
            metric=f"factor_scores.{asset.symbol}",
            value=factor,
            methodology="Standardized factor scores in [-1,1] (STUB).",
            parameters={"factors": list(factor)},
            model_version=analytics.MODEL_VERSION,
        )
    )

    # 3. NARRATIVE — retrieve evidence, build a GROUNDED prompt, cite everything
    evidence = ResearchAgent(llm).gather(asset.symbol, actx)
    grounded = _grounded_context(env, evidence)
    result = ResearchAgent(llm).synthesize(symbol=asset.symbol, grounded_prompt=grounded, ctx=actx)
    citations = [f"obs:{o.field}" for o in env.observed] + [e.citation_id for e in evidence]
    env.narrative.append(Narrative(text=result.text, citations=citations, kind="interpretation", section="summary"))
    gctx.models = [
        {"name": result.model_name, "version": result.model_version},
        {"name": "risk-core", "version": analytics.MODEL_VERSION},
    ]

    return apply(env, gctx)


# --- 2. portfolio analysis --------------------------------------------------
def analyze_portfolio(*, portfolio: Portfolio, gctx: GuardrailContext, scenarios: list[dict] | None = None) -> Envelope:
    llm = get_llm()
    env = Envelope(language=gctx.language)

    # Build weighted holdings from raw prices (OBSERVED) → weights.
    holdings: list[analytics.WeightedHolding] = []
    class_weights: dict[str, float] = {}
    market_values: dict[str, float] = {}
    total_mv = 0.0
    resolved: list[tuple[Asset, float]] = []

    for pos in portfolio.positions:
        asset = repo.assets.get(pos.asset_id)
        if not asset:
            continue
        bars = repo.latest_prices(asset.id, limit=252)
        if not bars:
            continue
        mv = pos.quantity * bars[-1].close
        market_values[asset.symbol] = mv
        total_mv += mv
        resolved.append((asset, mv))
        env.observed.append(_observed_price(asset))  # type: ignore[arg-type]

    for asset, mv in resolved:
        weight = mv / total_mv if total_mv else 0.0
        bars = repo.latest_prices(asset.id, limit=252)
        closes = [b.close for b in bars]
        returns = analytics._returns_from_closes(closes)
        holdings.append(
            analytics.WeightedHolding(
                symbol=asset.symbol,
                weight=weight,
                returns=returns,
                factor_scores=_factor_scores_for(asset),
            )
        )
        class_weights[asset.asset_class] = class_weights.get(asset.asset_class, 0.0) + weight

    # 2. DERIVED — the deterministic quant core
    conc = analytics.concentration(holdings)
    fexp = analytics.factor_exposure(holdings)
    dside = analytics.downside_risk(holdings)
    for d in (conc, fexp, dside):
        env.derived.append(
            Derived(
                metric=d["metric"],
                value=d["value"],
                methodology=d["methodology"],
                parameters=d["parameters"],
                model_version=d["model_version"],
            )
        )

    # scenarios (SPECULATIVE — marked as such by both the core and the guardrail)
    for spec in scenarios or []:
        sc = analytics.scenario(class_weights, spec.get("shocks", {}), spec.get("name", "scenario"))
        env.derived.append(
            Derived(
                metric=sc["metric"],
                value=sc["value"],
                methodology=sc["methodology"],
                parameters=sc["parameters"],
                model_version=sc["model_version"],
            )
        )
        env.narrative.append(
            Narrative(
                text=f"Under scenario '{spec.get('name')}', estimated portfolio return is "
                f"{sc['value']['estimated_return']:.2%} (first-order estimate).",
                citations=[f"der:{sc['metric']}"],
                kind="scenario",
                speculative=True,
                section="scenarios",
            )
        )

    # 3. NARRATIVE — explain the DERIVED numbers (grounded, cited)
    grounded = _grounded_context(env, [])
    system = "Explain the portfolio's risk metrics in plain language. Cite each metric. No advice."
    result = llm.complete(system=system, prompt=grounded, language=gctx.language)
    env.narrative.insert(
        0,
        Narrative(
            text=result.text,
            citations=[f"der:{d.metric}" for d in env.derived if not d.metric.startswith("scenario")],
            kind="interpretation",
            section="risk_summary",
        ),
    )
    gctx.models = [
        {"name": result.model_name, "version": result.model_version},
        {"name": "risk-core", "version": analytics.MODEL_VERSION},
    ]
    gctx.parameters = {"scenarios": scenarios or []}

    return apply(env, gctx)


# --- 2b. portfolio construction ---------------------------------------------
# Target factor tilts per risk profile (illustrative; a real optimizer would
# solve under the full constraint set).
_PROFILE_TILT = {
    "conservative": {"quality": 1.0, "volatility": -1.0, "value": 0.5},
    "balanced": {"quality": 0.5, "momentum": 0.3, "value": 0.3},
    "growth": {"growth": 1.0, "momentum": 0.8, "quality": 0.2},
}


def construct_portfolio(
    *, assets: list[Asset], risk_profile: str, max_position_weight: float, gctx: GuardrailContext
) -> Envelope:
    """Suggest model-portfolio weights under constraints. Suggestions only."""
    llm = get_llm()
    env = Envelope(language=gctx.language)
    tilt = _PROFILE_TILT.get(risk_profile, _PROFILE_TILT["balanced"])

    # Score each asset by alignment with the profile's factor tilt.
    raw_scores: dict[str, float] = {}
    for asset in assets:
        factors = _factor_scores_for(asset)
        score = sum(tilt.get(f, 0.0) * v for f, v in factors.items())
        raw_scores[asset.symbol] = max(score, 0.01)  # keep positive for weighting

    total = sum(raw_scores.values()) or 1.0
    weights = {s: v / total for s, v in raw_scores.items()}
    # Enforce the max-position-weight constraint, redistributing the excess.
    weights = _cap_weights(weights, max_position_weight)

    env.derived.append(
        Derived(
            metric="target_weights",
            value={s: round(w, 4) for s, w in weights.items()},
            methodology="Factor-tilt score per risk profile, normalized to weights, "
            "capped at max_position_weight with excess redistributed pro-rata.",
            parameters={"risk_profile": risk_profile, "max_position_weight": max_position_weight},
            model_version=analytics.MODEL_VERSION,
        )
    )
    system = (
        "Explain the suggested model-portfolio construction in plain language. "
        "Cite the target weights. This is a suggestion, not personalized advice."
    )
    result = llm.complete(system=system, prompt=_grounded_context(env, []), language=gctx.language)
    env.narrative.append(
        Narrative(text=result.text, citations=["der:target_weights"], kind="interpretation", section="construction")
    )
    gctx.models = [
        {"name": result.model_name, "version": result.model_version},
        {"name": "risk-core", "version": analytics.MODEL_VERSION},
    ]
    gctx.parameters = {"risk_profile": risk_profile, "max_position_weight": max_position_weight}
    return apply(env, gctx)


def _cap_weights(weights: dict[str, float], cap: float) -> dict[str, float]:
    """Cap each weight at ``cap``, redistributing excess to uncapped names."""
    w = dict(weights)
    for _ in range(len(w)):  # iterate to convergence (bounded)
        excess = sum(v - cap for v in w.values() if v > cap)
        if excess <= 1e-9:
            break
        uncapped = {k: v for k, v in w.items() if v < cap}
        room = sum(cap - v for v in uncapped.values()) or 1.0
        for k in w:
            if w[k] >= cap:
                w[k] = cap
            elif k in uncapped:
                w[k] += excess * (cap - uncapped[k]) / room
    return w


# --- 3. signal generation ---------------------------------------------------
def generate_signal(*, asset: Asset, horizon: str, gctx: GuardrailContext) -> dict:
    llm = get_llm()
    bars = repo.latest_prices(asset.id, limit=60)
    closes = [b.close for b in bars] or [100.0]
    last = closes[-1]
    ma20 = sum(closes[-20:]) / min(20, len(closes))
    direction = "long" if last > ma20 else "neutral"
    stop = round(last * 0.94, 2)
    target = round(last * 1.12, 2)
    rr = round((target - last) / (last - stop), 2) if last != stop else None

    evidence = retriever.retrieve(asset_symbol=asset.symbol, language=gctx.language)
    catalysts = [e.text for e in evidence][:3]

    env = Envelope(language=gctx.language)
    env.observed.append(_observed_price(asset))  # type: ignore[arg-type]
    env.derived.append(
        Derived(
            metric=f"trend.{asset.symbol}",
            value={"last": last, "ma20": round(ma20, 2)},
            methodology="Price vs 20-day moving average.",
            parameters={"window": 20},
            model_version=analytics.MODEL_VERSION,
        )
    )
    system = "Write a concise, non-advisory trade thesis grounded in the provided facts. Cite them."
    thesis_res = llm.complete(system=system, prompt=_grounded_context(env, evidence), language=gctx.language)
    env.narrative.append(
        Narrative(
            text=thesis_res.text,
            citations=[f"obs:price.close.{asset.symbol}", f"der:trend.{asset.symbol}"]
            + [e.citation_id for e in evidence],
            kind="interpretation",
            section="thesis",
        )
    )
    gctx.models = [{"name": thesis_res.model_name, "version": thesis_res.model_version}]
    gctx.parameters = {"horizon": horizon}
    env = apply(env, gctx)

    return {
        "symbol": asset.symbol,
        "direction": direction,
        "thesis": env.narrative[0].text if env.narrative else "",
        "risk_reward": {"entry": last, "stop": stop, "target": target, "rr_ratio": rr},
        "key_levels": {"support": stop, "resistance": target, "ma20": round(ma20, 2)},
        "catalysts": catalysts,
        "confidence": 0.55 if direction == "long" else 0.4,
        "audit_record_id": env.audit_record_id,
        "disclaimers": env.disclaimers,
    }


# --- 4. report generation ---------------------------------------------------
def generate_report(*, kind: str, subject_type: str, subject_id: str, gctx: GuardrailContext) -> dict:
    """Assemble a client-ready report. Runs async in prod (queue + webhook)."""
    if subject_type == "asset":
        asset = repo.assets.get(subject_id) or repo.asset_by_symbol(subject_id)
        if not asset:
            raise ValueError("unknown asset")
        env = generate_asset_deep_dive(asset=asset, gctx=gctx)
    elif subject_type == "portfolio":
        pf = repo.portfolios.get(subject_id)
        if not pf:
            raise ValueError("unknown portfolio")
        env = analyze_portfolio(portfolio=pf, gctx=gctx)
    else:
        raise ValueError(f"unsupported subject_type {subject_type}")

    return {
        "kind": kind,
        "language": gctx.language,
        "generated_at": datetime.now(UTC).isoformat(),
        "sections": {
            "observed": [o.model_dump(mode="json") for o in env.observed],
            "derived": [d.model_dump() for d in env.derived],
            "narrative": [n.model_dump() for n in env.narrative],
        },
        "disclaimers": env.disclaimers,
        "audit_record_id": env.audit_record_id,
    }


# --- grounding --------------------------------------------------------------
def _grounded_context(env: Envelope, evidence) -> str:
    """Assemble the ONLY context the LLM may use: observed facts, derived
    metrics, and retrieved evidence — each labelled so citations map back."""
    lines: list[str] = ["FACTS (observed):"]
    for o in env.observed:
        lines.append(f"  - [obs:{o.field}] {o.value} {o.unit or ''} (source {o.source}, as_of {o.as_of:%Y-%m-%d})")
    lines.append("METRICS (derived):")
    for d in env.derived:
        lines.append(f"  - [der:{d.metric}] {d.value}  // {d.methodology}")
    if evidence:
        lines.append("EVIDENCE (retrieved):")
        for e in evidence:
            lines.append(f"  - [{e.citation_id}] {e.text} (source {e.source}, {e.published_at:%Y-%m-%d})")
    return "\n".join(lines)
