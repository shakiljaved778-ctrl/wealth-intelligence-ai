"""Data connectors → canonical schema.

STUB: real deployments implement one adapter per provider (market, fundamental,
alternative) that fetches and normalizes into the canonical entities in
``app.models``. Every adapter must:
  * run each instrument through ``policy.check_instrument`` before ingest;
  * write raw facts append-only (never mutate);
  * stamp ``source`` and a timestamp on every record.

Here we generate deterministic mock data so the scaffold runs offline.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from app.models import Asset, FundamentalSnapshot, PriceBar
from app.services.data.policy import check_instrument


def ingest_asset(
    *, symbol: str, name: str, asset_class: str, currency: str = "USD", metadata: dict | None = None
) -> Asset:
    metadata = metadata or {}
    verdict = check_instrument(symbol=symbol, name=name, asset_class=asset_class, metadata=metadata)
    if not verdict.allowed:
        # Disallowed instruments never enter the canonical store.
        raise ValueError(f"policy rejected {symbol}: {verdict.reason}")
    return Asset(
        symbol=symbol,
        name=name,
        asset_class=asset_class,  # type: ignore[arg-type]
        currency=currency,
        metadata=metadata,
    )


def mock_price_history(asset_id: str, *, days: int = 260, seed: float = 100.0) -> list[PriceBar]:
    """Deterministic synthetic OHLCV (STUB for a real market-data feed)."""
    bars: list[PriceBar] = []
    start = datetime.now(UTC) - timedelta(days=days)
    price = seed
    h = (hash(asset_id) % 1000) / 1000.0
    for i in range(days):
        # smooth, reproducible path — no randomness so tests are stable
        drift = 0.0004 + 0.001 * math.sin((i / 30.0) + h * 6.28)
        price *= 1 + drift
        close = round(price, 4)
        bars.append(
            PriceBar(
                asset_id=asset_id,
                interval="1d",
                ts=start + timedelta(days=i),
                open=round(close * 0.998, 4),
                high=round(close * 1.006, 4),
                low=round(close * 0.994, 4),
                close=close,
                volume=1_000_000 + (i % 7) * 50_000,
                source="stub-market",
            )
        )
    return bars


def mock_fundamentals(asset_id: str) -> FundamentalSnapshot:
    """Deterministic synthetic fundamentals (STUB)."""
    return FundamentalSnapshot(
        asset_id=asset_id,
        as_of=datetime.now(UTC) - timedelta(days=20),
        period="Q",
        statements={"revenue": 26_000_000_000, "net_income": 9_200_000_000},
        estimates={"eps_next_q": 4.6, "revenue_growth_yoy": 0.22},
        ratios={"pe": 42.1, "pb": 18.4, "gross_margin": 0.73, "debt_to_equity": 0.31},
        source="stub-fundamentals",
    )
