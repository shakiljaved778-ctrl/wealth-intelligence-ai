"""Product policy filter, applied at the *ingestion boundary*.

The 'no crypto, no leverage' rule is enforced here so disallowed instruments
never enter the canonical store — and re-checked later in the guardrail layer
(defence in depth). See docs/05-compliance.md.
"""

from __future__ import annotations

from dataclasses import dataclass

# Asset classes the platform is licensed/positioned to cover.
ALLOWED_ASSET_CLASSES = {"equity", "etf", "bond", "fund", "fx", "macro"}

# Signals that an instrument is crypto or leveraged (blocked).
_CRYPTO_MARKERS = {"crypto", "btc", "eth", "coin", "token", "-usd-crypto"}
_LEVERAGE_MARKERS = {
    "leveraged",
    "2x",
    "3x",
    "-1x",
    "ultra",
    "ultrapro",
    "margin",
    "geared",
}


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    reason: str | None = None


def check_instrument(*, symbol: str, name: str, asset_class: str, metadata: dict) -> PolicyResult:
    """Return whether an instrument may be ingested."""
    if asset_class not in ALLOWED_ASSET_CLASSES:
        return PolicyResult(False, f"asset_class '{asset_class}' not permitted")

    haystack = f"{symbol} {name} {metadata.get('description', '')}".lower()
    tags = {str(t).lower() for t in metadata.get("tags", [])}

    if metadata.get("is_crypto") or tags & _CRYPTO_MARKERS or any(m in haystack for m in _CRYPTO_MARKERS):
        return PolicyResult(False, "crypto instruments are not permitted (NO_CRYPTO)")

    if (
        metadata.get("is_leveraged")
        or metadata.get("leverage_factor", 1) not in (1, 1.0)
        or tags & _LEVERAGE_MARKERS
        or any(m in haystack for m in _LEVERAGE_MARKERS)
    ):
        return PolicyResult(False, "leveraged products are not permitted (NO_LEVERAGE)")

    return PolicyResult(True)
