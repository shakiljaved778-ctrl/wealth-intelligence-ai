"""Agent framework.

In production these are nodes in a LangGraph state graph over LlamaIndex
retrievers, each with typed I/O and a shared, audited context
(see docs/04-ai-engine.md §4.2). Here they are plain classes with the same
responsibilities so the orchestration in ``engine.py`` reads the same way it
will once the graph is wired.

Agents never assert facts they fetched themselves — they consume the canonical
feature store + the deterministic quant core, so provenance is attributable.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.ai.llm import LLM, get_llm
from app.services.ai.rag import Evidence, retriever


@dataclass
class AgentContext:
    language: str = "en"
    entitlements: set[str] | None = None


class ResearchAgent:
    """Asset/issuer deep-dives: gather evidence, synthesize a grounded read."""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or get_llm()

    def gather(self, symbol: str, ctx: AgentContext) -> list[Evidence]:
        return retriever.retrieve(asset_symbol=symbol, language=ctx.language, entitlements=ctx.entitlements)

    def synthesize(self, *, symbol: str, grounded_prompt: str, ctx: AgentContext):
        system = (
            "You are a financial research assistant. Explain and contextualize ONLY the "
            "facts and metrics provided. Do not invent numbers. Cite every factual claim."
        )
        return self.llm.complete(system=system, prompt=grounded_prompt, language=ctx.language)


class PortfolioAgent:
    """Construction / optimization / rebalancing SUGGESTIONS (never execution)."""

    def rebalance_suggestions(self, current: dict[str, float], targets: dict[str, float]):
        return {sym: round(targets.get(sym, 0.0) - current.get(sym, 0.0), 4) for sym in set(current) | set(targets)}


class SignalAgent:
    """Trade-idea generation: thesis + risk/reward + levels + catalysts."""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or get_llm()


class MonitoringAgent:
    """Watchlist monitoring: detect material change, raise alerts."""

    def assess_materiality(self, evidence: list[Evidence]) -> str:
        # STUB heuristic: filings/news within the window are 'material'.
        if any(e.doc_type in ("filing", "news") for e in evidence):
            return "material"
        return "info"


class ReportingAgent:
    """Assemble client-ready reports (EN/AR) from the other agents' outputs."""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or get_llm()
