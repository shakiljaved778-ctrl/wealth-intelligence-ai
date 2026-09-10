"""Seed the in-memory repository with demo data for local exploration.

Creates a demo org + user, a *policy-compliant* multi-asset-class universe
(crypto/leveraged instruments are rejected by the ingest policy), each with raw
price history and — for issuers — fundamentals, plus demo portfolios and a
watchlist. Returns a ready-to-use access token so `/docs` is exercisable
immediately. All data is deterministic mock data (no real market feed).
"""

from __future__ import annotations

from app.core.security import create_token, hash_password
from app.models import Organization, Portfolio, Position, User, Watchlist
from app.repository import repo
from app.services.data import connectors

# symbol, name, asset_class, currency
_SEED_ASSETS = [
    ("NVDA", "NVIDIA Corporation", "equity", "USD"),
    ("AAPL", "Apple Inc.", "equity", "USD"),
    ("MSFT", "Microsoft Corporation", "equity", "USD"),
    ("SPY", "SPDR S&P 500 ETF Trust", "etf", "USD"),
    ("AGG", "iShares Core US Aggregate Bond ETF", "etf", "USD"),
    ("QNBK", "Qatar National Bank", "equity", "QAR"),
    ("IQCD", "Industries Qatar", "equity", "QAR"),
    ("USDQAR", "US Dollar / Qatari Riyal", "fx", "QAR"),
    ("BRENT", "Brent Crude Oil", "macro", "USD"),
]


def seed() -> str:
    if repo.organizations:
        # already seeded
        org = next(iter(repo.organizations.values()))
        user = next(iter(repo.users.values()))
        return create_token(user.id, scopes=["read", "write", "admin"], org_id=org.id)

    org = repo.add_org(
        Organization(
            name="Demo Bank",
            type="bank",
            data_region="qa",
            tier="professional",
            licensing_context={"advice": False},
        )
    )
    user = repo.add_user(
        User(
            organization_id=org.id,
            email="demo@wealthintelligence.ai",
            hashed_password=hash_password("demo1234"),
            role="admin",
            locale="en",
            segmentation="professional",
        )
    )

    for symbol, name, asset_class, currency in _SEED_ASSETS:
        asset = connectors.ingest_asset(symbol=symbol, name=name, asset_class=asset_class, currency=currency)
        repo.add_asset(asset)
        repo.append_prices(connectors.mock_price_history(asset.id, symbol=symbol))
        snap = connectors.mock_fundamentals(asset.id, symbol=symbol)
        if snap is not None:  # ETFs / FX / macro have no issuer fundamentals
            repo.append_fundamentals(snap)

    def _id(sym: str) -> str:
        a = repo.asset_by_symbol(sym)
        assert a is not None
        return a.id

    # A diversified model portfolio and a Qatar-tilted one.
    repo.add_portfolio(
        Portfolio(
            organization_id=org.id,
            owner_user_id=user.id,
            name="Demo Balanced",
            kind="model",
            base_currency="USD",
            constraints={"max_position_weight": 0.4, "sector_cap": 0.5},
            positions=[
                Position(asset_id=_id("NVDA"), quantity=100),
                Position(asset_id=_id("MSFT"), quantity=60),
                Position(asset_id=_id("SPY"), quantity=200),
                Position(asset_id=_id("AGG"), quantity=300),
            ],
        )
    )
    repo.add_portfolio(
        Portfolio(
            organization_id=org.id,
            owner_user_id=user.id,
            name="Qatar Income",
            kind="model",
            base_currency="QAR",
            constraints={"max_position_weight": 0.5, "sector_cap": 0.7},
            positions=[
                Position(asset_id=_id("QNBK"), quantity=5000),
                Position(asset_id=_id("IQCD"), quantity=4000),
            ],
        )
    )

    # A demo watchlist so /watchlists/{id}/scan raises alerts out of the box.
    repo.add_watchlist(
        Watchlist(
            organization_id=org.id,
            owner_user_id=user.id,
            name="Tech & Qatar",
            asset_ids=[_id("NVDA"), _id("QNBK")],
        )
    )

    return create_token(user.id, scopes=["read", "write", "admin"], org_id=org.id)
