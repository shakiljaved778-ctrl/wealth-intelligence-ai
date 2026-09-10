"""Domain entities. Mirror docs/02-data-model.md.

Pydantic models here double as the ORM-free representation used by the in-memory
repository. Swap for SQLAlchemy models when wiring a real database — the shapes
are chosen to map cleanly to tables.
"""

from app.models.entities import (
    Alert,
    ApiKey,
    Asset,
    ComplianceRule,
    FundamentalSnapshot,
    Organization,
    Portfolio,
    Position,
    PriceBar,
    Report,
    Signal,
    UsageRecord,
    User,
    Watchlist,
    Webhook,
)

__all__ = [
    "Alert",
    "ApiKey",
    "Asset",
    "ComplianceRule",
    "FundamentalSnapshot",
    "Organization",
    "Portfolio",
    "Position",
    "PriceBar",
    "Report",
    "Signal",
    "UsageRecord",
    "User",
    "Watchlist",
    "Webhook",
]
