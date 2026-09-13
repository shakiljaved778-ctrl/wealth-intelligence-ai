"""Core domain entities (see docs/02-data-model.md)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    return datetime.now(UTC)


AssetClass = Literal["equity", "etf", "bond", "fund", "fx", "macro"]


class Organization(BaseModel):
    id: str = Field(default_factory=lambda: _id("org"))
    name: str
    type: Literal["bank", "broker", "prop", "fintech", "b2c"] = "b2c"
    data_region: Literal["qa", "eu", "global"] = "global"
    tier: Literal["starter", "professional", "enterprise"] = "starter"
    licensing_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class User(BaseModel):
    id: str = Field(default_factory=lambda: _id("usr"))
    organization_id: str
    email: str
    hashed_password: str | None = None
    role: Literal["admin", "analyst", "advisor", "client", "viewer"] = "client"
    locale: Literal["en", "ar"] = "en"
    # Segmentation gates personalized advice language (see compliance blueprint).
    segmentation: Literal["retail", "professional", "eligible_counterparty"] = "retail"
    risk_profile: dict[str, Any] = Field(default_factory=dict)
    investment_objectives: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Asset(BaseModel):
    id: str = Field(default_factory=lambda: _id("ast"))
    symbol: str
    name: str
    asset_class: AssetClass
    isin: str | None = None
    exchange: str | None = None
    currency: str = "USD"
    country: str | None = None
    sector: str | None = None
    industry: str | None = None
    # Set False (or blocked at ingest) for disallowed instruments — see policy.py
    is_tradable_policy_ok: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class PriceBar(BaseModel):
    """Immutable OHLCV. Corrections append a new version — never mutate."""

    asset_id: str
    interval: Literal["1m", "5m", "1h", "1d"] = "1d"
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    ingested_at: datetime = Field(default_factory=_now)
    version: int = 1


class FundamentalSnapshot(BaseModel):
    """Immutable point-in-time fundamentals."""

    asset_id: str
    as_of: datetime
    period: Literal["Q", "A"] = "Q"
    statements: dict[str, Any] = Field(default_factory=dict)
    estimates: dict[str, Any] = Field(default_factory=dict)
    ratios: dict[str, Any] = Field(default_factory=dict)  # raw provider ratios
    source: str = "stub"
    ingested_at: datetime = Field(default_factory=_now)
    version: int = 1


class Position(BaseModel):
    asset_id: str
    quantity: float
    cost_basis: float | None = None
    as_of: datetime = Field(default_factory=_now)


class Portfolio(BaseModel):
    id: str = Field(default_factory=lambda: _id("pf"))
    organization_id: str
    owner_user_id: str | None = None
    name: str
    base_currency: str = "USD"
    kind: Literal["model", "client", "custom"] = "custom"
    constraints: dict[str, Any] = Field(default_factory=dict)
    positions: list[Position] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Signal(BaseModel):
    id: str = Field(default_factory=lambda: _id("sig"))
    asset_id: str
    created_at: datetime = Field(default_factory=_now)
    status: Literal["active", "triggered", "closed", "expired"] = "active"
    direction: Literal["long", "short", "neutral"] = "neutral"
    thesis: str = ""
    risk_reward: dict[str, Any] = Field(default_factory=dict)
    key_levels: dict[str, Any] = Field(default_factory=dict)
    catalysts: list[str] = Field(default_factory=list)
    horizon: str = "swing"
    confidence: float = 0.5
    audit_record_id: str | None = None


class Report(BaseModel):
    id: str = Field(default_factory=lambda: _id("rep"))
    organization_id: str
    subject_type: Literal["asset", "portfolio", "watchlist"]
    subject_id: str
    kind: Literal["deep_dive", "portfolio_analysis", "client_report", "memo"]
    language: Literal["en", "ar"] = "en"
    status: Literal["queued", "generating", "ready", "failed"] = "queued"
    content: dict[str, Any] | None = None
    audit_record_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
    ready_at: datetime | None = None


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: _id("alt"))
    organization_id: str
    user_id: str | None = None
    subject_type: Literal["asset", "portfolio", "watchlist"]
    subject_id: str
    trigger: dict[str, Any] = Field(default_factory=dict)
    severity: Literal["info", "material", "critical"] = "info"
    message: str = ""
    delivered_channels: list[str] = Field(default_factory=list)
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class ComplianceRule(BaseModel):
    id: str = Field(default_factory=lambda: _id("rule"))
    organization_id: str | None = None  # None = global default
    code: str
    params: dict[str, Any] = Field(default_factory=dict)
    severity: Literal["block", "warn"] = "block"
    enabled: bool = True


class ApiKey(BaseModel):
    id: str = Field(default_factory=lambda: _id("key"))
    organization_id: str
    name: str
    hashed_key: str
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    rate_limit_per_min: int = 120
    revoked: bool = False
    created_at: datetime = Field(default_factory=_now)


class UsageRecord(BaseModel):
    organization_id: str
    api_key_id: str | None = None
    user_id: str | None = None
    endpoint: str
    units: int = 1
    ts: datetime = Field(default_factory=_now)


class Watchlist(BaseModel):
    id: str = Field(default_factory=lambda: _id("wl"))
    organization_id: str
    owner_user_id: str | None = None
    name: str
    asset_ids: list[str] = Field(default_factory=list)
    # Alert rule thresholds evaluated by the monitoring agent.
    rules: dict[str, Any] = Field(default_factory=lambda: {"news_filings": True, "price_move_pct": 5.0})
    created_at: datetime = Field(default_factory=_now)


class Webhook(BaseModel):
    id: str = Field(default_factory=lambda: _id("wh"))
    organization_id: str
    url: str
    events: list[str] = Field(default_factory=lambda: ["alert.raised"])
    # Signing secret; deliveries carry X-WIA-Signature = HMAC-SHA256(secret, body).
    secret: str = ""
    active: bool = True
    created_at: datetime = Field(default_factory=_now)
