"""Data connectors → canonical schema.

STUB: real deployments implement one adapter per provider (market, fundamental,
alternative) that fetches and normalizes into the canonical entities in
``app.models``. Every adapter must:
  * run each instrument through ``policy.check_instrument`` before ingest;
  * write raw facts append-only (never mutate);
  * stamp ``source`` and a timestamp on every record.

Here we generate deterministic, per-symbol mock data so the scaffold runs fully
offline with a realistic, varied demo universe (no real market-data feed).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models import Asset, FundamentalSnapshot, PriceBar
from app.services.data.policy import check_instrument

# Per-symbol mock profiles. Each drives a distinct price path, sector/geography
# metadata, and (for issuers) fundamentals — so deep-dives, factor exposures and
# portfolio analytics differ meaningfully by asset. All values are illustrative.
_PROFILES: dict[str, dict[str, Any]] = {
    "NVDA": {
        "base": 118.0,
        "vol": 0.022,
        "trend": 0.0013,
        "sector": "Technology",
        "industry": "Semiconductors",
        "country": "US",
        "fundamentals": {
            "revenue": 30_040_000_000,
            "net_income": 16_600_000_000,
            "pe": 46.2,
            "pb": 24.1,
            "gross_margin": 0.75,
            "debt_to_equity": 0.22,
            "eps_next_q": 0.74,
            "revenue_growth_yoy": 1.22,
        },
    },
    "AAPL": {
        "base": 225.0,
        "vol": 0.014,
        "trend": 0.0005,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "US",
        "fundamentals": {
            "revenue": 85_800_000_000,
            "net_income": 21_400_000_000,
            "pe": 33.5,
            "pb": 51.2,
            "gross_margin": 0.46,
            "debt_to_equity": 1.51,
            "eps_next_q": 1.39,
            "revenue_growth_yoy": 0.05,
        },
    },
    "MSFT": {
        "base": 415.0,
        "vol": 0.013,
        "trend": 0.0006,
        "sector": "Technology",
        "industry": "Software",
        "country": "US",
        "fundamentals": {
            "revenue": 64_700_000_000,
            "net_income": 22_000_000_000,
            "pe": 35.1,
            "pb": 11.8,
            "gross_margin": 0.70,
            "debt_to_equity": 0.33,
            "eps_next_q": 2.93,
            "revenue_growth_yoy": 0.15,
        },
    },
    "SPY": {
        "base": 545.0,
        "vol": 0.010,
        "trend": 0.0004,
        "sector": "Diversified",
        "industry": "US Large-Cap Blend ETF",
        "country": "US",
        # ETFs carry no issuer fundamentals; left absent on purpose.
    },
    "AGG": {
        "base": 99.0,
        "vol": 0.004,
        "trend": 0.00005,
        "sector": "Fixed Income",
        "industry": "US Aggregate Bond ETF",
        "country": "US",
    },
    "QNBK": {
        "base": 16.2,
        "vol": 0.011,
        "trend": 0.0003,
        "sector": "Financials",
        "industry": "Banks",
        "country": "QA",
        "fundamentals": {
            "revenue": 8_100_000_000,
            "net_income": 1_150_000_000,
            "pe": 11.4,
            "pb": 1.6,
            "gross_margin": 0.0,
            "debt_to_equity": 0.0,
            "eps_next_q": 0.42,
            "revenue_growth_yoy": 0.08,
        },
    },
    "IQCD": {
        "base": 17.4,
        "vol": 0.012,
        "trend": 0.0002,
        "sector": "Materials",
        "industry": "Petrochemicals",
        "country": "QA",
        "fundamentals": {
            "revenue": 4_300_000_000,
            "net_income": 720_000_000,
            "pe": 15.2,
            "pb": 2.1,
            "gross_margin": 0.31,
            "debt_to_equity": 0.12,
            "eps_next_q": 0.19,
            "revenue_growth_yoy": -0.03,
        },
    },
    "USDQAR": {
        "base": 3.64,
        "vol": 0.0006,
        "trend": 0.0,
        "sector": "FX",
        "industry": "USD/QAR (pegged)",
        "country": "QA",
    },
    "BRENT": {
        "base": 82.0,
        "vol": 0.018,
        "trend": 0.0,
        "sector": "Macro",
        "industry": "Brent Crude (macro series)",
        "country": "GL",
    },
}

_DEFAULT = {"base": 100.0, "vol": 0.012, "trend": 0.0004, "sector": None, "industry": None, "country": None}


def profile_for(symbol: str) -> dict[str, Any]:
    return _PROFILES.get(symbol.upper(), _DEFAULT)


def ingest_asset(
    *, symbol: str, name: str, asset_class: str, currency: str = "USD", metadata: dict | None = None
) -> Asset:
    metadata = metadata or {}
    verdict = check_instrument(symbol=symbol, name=name, asset_class=asset_class, metadata=metadata)
    if not verdict.allowed:
        # Disallowed instruments never enter the canonical store.
        raise ValueError(f"policy rejected {symbol}: {verdict.reason}")
    p = profile_for(symbol)
    return Asset(
        symbol=symbol,
        name=name,
        asset_class=asset_class,  # type: ignore[arg-type]
        currency=currency,
        sector=p.get("sector"),
        industry=p.get("industry"),
        country=p.get("country"),
        metadata=metadata,
    )


def mock_price_history(
    asset_id: str, *, symbol: str | None = None, days: int = 260, seed: float | None = None
) -> list[PriceBar]:
    """Deterministic synthetic OHLCV, shaped by the symbol's profile (STUB)."""
    p = profile_for(symbol or "")
    price = float(seed if seed is not None else p["base"])
    trend, vol = p["trend"], p["vol"]
    h = (hash(symbol or asset_id) % 1000) / 1000.0

    bars: list[PriceBar] = []
    start = datetime.now(UTC) - timedelta(days=days)
    for i in range(days):
        # smooth, reproducible path — deterministic so tests stay stable
        drift = trend + vol * 0.5 * math.sin((i / 30.0) + h * 6.28)
        price *= 1 + drift
        close = round(price, 4)
        span = max(vol, 0.002)
        bars.append(
            PriceBar(
                asset_id=asset_id,
                interval="1d",
                ts=start + timedelta(days=i),
                open=round(close * (1 - span * 0.2), 4),
                high=round(close * (1 + span * 0.5), 4),
                low=round(close * (1 - span * 0.5), 4),
                close=close,
                volume=1_000_000 + (i % 7) * 50_000 + int(h * 400_000),
                source="stub-market",
            )
        )
    return bars


def mock_fundamentals(asset_id: str, *, symbol: str | None = None) -> FundamentalSnapshot | None:
    """Deterministic synthetic fundamentals per issuer (STUB).

    Returns ``None`` for instruments without issuer fundamentals (ETFs, FX,
    macro series) so we never fabricate statements for them.
    """
    p = profile_for(symbol or "")
    f = p.get("fundamentals")
    if not f:
        return None
    return FundamentalSnapshot(
        asset_id=asset_id,
        as_of=datetime.now(UTC) - timedelta(days=20),
        period="Q",
        statements={"revenue": f["revenue"], "net_income": f["net_income"]},
        estimates={"eps_next_q": f["eps_next_q"], "revenue_growth_yoy": f["revenue_growth_yoy"]},
        ratios={
            "pe": f["pe"],
            "pb": f["pb"],
            "gross_margin": f["gross_margin"],
            "debt_to_equity": f["debt_to_equity"],
        },
        source="stub-fundamentals",
    )
