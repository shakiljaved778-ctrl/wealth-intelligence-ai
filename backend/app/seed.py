"""Seed the in-memory repository with demo data for local exploration.

Creates a demo org + user, a couple of *policy-compliant* assets (crypto/
leveraged instruments are rejected by the ingest policy), their raw price
history and fundamentals, and a demo portfolio. Returns a ready-to-use access
token so `/docs` can be exercised immediately.
"""

from __future__ import annotations

from app.core.security import create_token, hash_password
from app.models import Organization, Portfolio, Position, User
from app.repository import repo
from app.services.data import connectors

_SEED_ASSETS = [
    ("NVDA", "NVIDIA Corporation", "equity", "USD"),
    ("AAPL", "Apple Inc.", "equity", "USD"),
    ("SPY", "SPDR S&P 500 ETF Trust", "etf", "USD"),
    ("QNBK", "Qatar National Bank", "equity", "QAR"),
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

    for i, (symbol, name, asset_class, currency) in enumerate(_SEED_ASSETS):
        asset = connectors.ingest_asset(symbol=symbol, name=name, asset_class=asset_class, currency=currency)
        repo.add_asset(asset)
        repo.append_prices(connectors.mock_price_history(asset.id, seed=80 + i * 40))
        repo.append_fundamentals(connectors.mock_fundamentals(asset.id))

    nvda = repo.asset_by_symbol("NVDA")
    spy = repo.asset_by_symbol("SPY")
    repo.add_portfolio(
        Portfolio(
            organization_id=org.id,
            owner_user_id=user.id,
            name="Demo Balanced",
            kind="model",
            constraints={"max_position_weight": 0.4, "sector_cap": 0.5},
            positions=[
                Position(asset_id=nvda.id, quantity=100),
                Position(asset_id=spy.id, quantity=200),
            ],
        )
    )

    return create_token(user.id, scopes=["read", "write", "admin"], org_id=org.id)
