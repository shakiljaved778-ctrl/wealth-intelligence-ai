"""Deterministic quant core — computes *derived* metrics.

Derived metrics are computed here (not by free-form LLM arithmetic) so every
number carries an explicit methodology + parameters + model version and can be
reproduced. The AI engine may *explain* these numbers but never *change* them.
See docs/04-ai-engine.md §4.3.

The maths is intentionally simple/standard (no numpy dependency) so the scaffold
runs anywhere. Replace with a vetted quant library for production.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

MODEL_VERSION = "risk-core-v0.1"

# Standard factor set (see docs/02-data-model.md FactorExposure).
FACTORS = ["value", "growth", "momentum", "quality", "size", "volatility"]


@dataclass
class WeightedHolding:
    symbol: str
    weight: float  # portfolio weight (0..1)
    returns: list[float] = field(default_factory=list)  # periodic returns
    factor_scores: dict[str, float] = field(default_factory=dict)


def _returns_from_closes(closes: list[float]) -> list[float]:
    return [(closes[i] / closes[i - 1]) - 1.0 for i in range(1, len(closes)) if closes[i - 1]]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ---- concentration ---------------------------------------------------------
def concentration(holdings: list[WeightedHolding]) -> dict[str, Any]:
    """Herfindahl-Hirschman Index + top-N weight."""
    weights = sorted((h.weight for h in holdings), reverse=True)
    hhi = sum(w * w for w in weights)
    return {
        "metric": "concentration",
        "value": {
            "hhi": round(hhi, 4),
            "effective_holdings": round(1 / hhi, 2) if hhi else 0,
            "top1_weight": round(weights[0], 4) if weights else 0,
            "top5_weight": round(sum(weights[:5]), 4),
        },
        "methodology": "Herfindahl-Hirschman Index over position weights; effective_holdings = 1/HHI.",
        "parameters": {"n_positions": len(holdings)},
        "model_version": MODEL_VERSION,
    }


# ---- factor exposure -------------------------------------------------------
def factor_exposure(holdings: list[WeightedHolding]) -> dict[str, Any]:
    """Weighted average of per-asset factor scores."""
    exposures = {f: 0.0 for f in FACTORS}
    for h in holdings:
        for f in FACTORS:
            exposures[f] += h.weight * h.factor_scores.get(f, 0.0)
    return {
        "metric": "factor_exposure",
        "value": {f: round(v, 4) for f, v in exposures.items()},
        "methodology": "Portfolio factor exposure = Σ (weight_i × factor_score_i), "
        "standardized factor scores in [-3, 3].",
        "parameters": {"factors": FACTORS},
        "model_version": MODEL_VERSION,
    }


# ---- downside risk ---------------------------------------------------------
def downside_risk(holdings: list[WeightedHolding], *, confidence: float = 0.95) -> dict[str, Any]:
    """Portfolio volatility, historical VaR, and max drawdown of the weighted path."""
    n = min((len(h.returns) for h in holdings if h.returns), default=0)
    if n == 0:
        return {
            "metric": "downside_risk",
            "value": {"annualized_vol": None, "var": None, "max_drawdown": None},
            "methodology": "insufficient return history",
            "parameters": {"confidence": confidence},
            "model_version": MODEL_VERSION,
        }
    port_returns = [sum(h.weight * h.returns[-n:][i] for h in holdings if h.returns) for i in range(n)]
    vol = _stdev(port_returns) * math.sqrt(252)
    ordered = sorted(port_returns)
    var_idx = max(0, int((1 - confidence) * len(ordered)) - 1)
    hist_var = -ordered[var_idx]

    # max drawdown of the cumulative path
    cum, peak, mdd = 1.0, 1.0, 0.0
    for r in port_returns:
        cum *= 1 + r
        peak = max(peak, cum)
        mdd = min(mdd, (cum / peak) - 1.0)

    return {
        "metric": "downside_risk",
        "value": {
            "annualized_vol": round(vol, 4),
            "var": round(hist_var, 4),
            "max_drawdown": round(mdd, 4),
        },
        "methodology": f"Annualized vol = stdev(daily) × √252; historical VaR at "
        f"{int(confidence * 100)}%; max drawdown of weighted cumulative path.",
        "parameters": {"confidence": confidence, "observations": n},
        "model_version": MODEL_VERSION,
    }


# ---- scenario / stress -----------------------------------------------------
# Illustrative factor sensitivities (β of asset-class return to each shock).
_SENSITIVITIES = {
    "rates_bps": {
        "equity": -0.0003,
        "bond": -0.0008,
        "etf": -0.0003,
        "fund": -0.0002,
        "fx": 0.0,
        "macro": 0.0,
    },
    "oil_pct": {
        "equity": 0.0015,
        "bond": -0.0005,
        "etf": 0.0010,
        "fund": 0.0008,
        "fx": 0.0,
        "macro": 0.0,
    },
    "fx_usd_pct": {
        "equity": -0.0020,
        "bond": -0.0010,
        "etf": -0.0015,
        "fund": -0.0012,
        "fx": 0.0100,
        "macro": 0.0,
    },
    "inflation_pct": {
        "equity": -0.0040,
        "bond": -0.0060,
        "etf": -0.0035,
        "fund": -0.0030,
        "fx": 0.0,
        "macro": 0.0,
    },
}


def scenario(holdings_by_class: dict[str, float], shocks: dict[str, float], name: str) -> dict[str, Any]:
    """Estimate portfolio P&L under a macro shock. Explicitly SPECULATIVE."""
    pnl = 0.0
    for shock, magnitude in shocks.items():
        sens = _SENSITIVITIES.get(shock, {})
        for asset_class, weight in holdings_by_class.items():
            pnl += weight * sens.get(asset_class, 0.0) * magnitude
    return {
        "metric": f"scenario:{name}",
        "value": {"estimated_return": round(pnl, 4)},
        "methodology": "First-order sensitivity model: ΔPnL = Σ weight × β(class,shock) × shock. "
        "Illustrative betas; forward-looking and SPECULATIVE.",
        "parameters": {"shocks": shocks},
        "model_version": MODEL_VERSION,
        "speculative": True,
    }
