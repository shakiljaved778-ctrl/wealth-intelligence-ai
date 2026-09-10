"""Retrieval layer (RAG).

Retrieval is ALWAYS scoped — never a global search — by asset/portfolio,
recency, language, entitlement, and data region (see docs/04-ai-engine.md §4.1).
Each retrieved chunk carries a stable ``citation_id`` so evidence maps 1:1 to
citations in the response envelope.

STUB: an in-memory corpus stands in for a vector index (pgvector / OpenSearch).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class Evidence:
    citation_id: str
    asset_symbol: str
    doc_type: str  # filing | news | research | macro | methodology
    published_at: datetime
    source: str
    language: str
    text: str


# Tiny illustrative corpus. Real corpus is ingested + embedded per §4.1.
_CORPUS: list[Evidence] = [
    Evidence(
        citation_id="doc:NVDA:filing:2025Q2",
        asset_symbol="NVDA",
        doc_type="filing",
        published_at=datetime(2025, 8, 28, tzinfo=UTC),
        source="issuer-10Q",
        language="en",
        text="Data center revenue grew year over year, driven by accelerated computing demand.",
    ),
    Evidence(
        citation_id="doc:NVDA:news:2025-09",
        asset_symbol="NVDA",
        doc_type="news",
        published_at=datetime(2025, 9, 2, tzinfo=UTC),
        source="newswire",
        language="en",
        text="Supply constraints on advanced packaging remain a watch item for the sector.",
    ),
]


class Retriever:
    def __init__(self, corpus: list[Evidence] | None = None) -> None:
        self._corpus = corpus if corpus is not None else _CORPUS

    def retrieve(
        self,
        *,
        asset_symbol: str,
        language: str = "en",
        as_of: datetime | None = None,
        entitlements: set[str] | None = None,
        limit: int = 5,
    ) -> list[Evidence]:
        as_of = as_of or datetime.now(UTC)
        results = [
            e
            for e in self._corpus
            if e.asset_symbol.upper() == asset_symbol.upper()
            and e.published_at <= as_of  # never leak future info into a historical view
            and (entitlements is None or e.doc_type in entitlements or e.doc_type == "methodology")
        ]
        # Prefer requested language; keep cross-language with a note handled upstream.
        results.sort(key=lambda e: (e.language != language, -e.published_at.timestamp()))
        return results[:limit]


retriever = Retriever()
