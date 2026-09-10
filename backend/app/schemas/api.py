"""Request/response schemas for the B2B API endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.envelope import Envelope

Language = Literal["en", "ar"]


# ---- Auth ------------------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=lambda: ["read"])


class ApiKeyCreated(BaseModel):
    id: str
    api_key: str  # shown once, at creation
    scopes: list[str]


# ---- Assets ----------------------------------------------------------------
class AssetOut(BaseModel):
    id: str
    symbol: str
    name: str
    asset_class: str
    currency: str
    country: str | None = None
    sector: str | None = None


class DeepDiveRequest(BaseModel):
    language: Language = "en"
    sections: list[str] | None = None
    portfolio_context: str | None = None


# ---- Portfolios ------------------------------------------------------------
class PositionIn(BaseModel):
    symbol: str
    quantity: float


class PortfolioCreate(BaseModel):
    name: str
    base_currency: str = "USD"
    kind: Literal["model", "client", "custom"] = "custom"
    constraints: dict[str, Any] = Field(default_factory=dict)
    positions: list[PositionIn] = Field(default_factory=list)


class PortfolioOut(BaseModel):
    id: str
    name: str
    base_currency: str
    kind: str
    constraints: dict[str, Any]
    positions: list[dict[str, Any]]


class ScenarioSpec(BaseModel):
    name: str
    shocks: dict[str, float]  # e.g. {"rates_bps": 100, "oil_pct": -20, "fx_usd_pct": 5}


class AnalyzeRequest(BaseModel):
    language: Language = "en"
    benchmarks: list[str] = Field(default_factory=list)
    scenarios: list[ScenarioSpec] = Field(default_factory=list)


class ConstructRequest(BaseModel):
    """Model-portfolio construction under constraints (suggestions only)."""

    universe: list[str] = Field(default_factory=list)  # symbols; empty = all seeded assets
    risk_profile: Literal["conservative", "balanced", "growth"] = "balanced"
    max_position_weight: float = 0.4
    language: Language = "en"


# ---- Signals ---------------------------------------------------------------
class SignalGenerateRequest(BaseModel):
    symbol: str
    horizon: Literal["intraday", "swing", "position"] = "swing"
    language: Language = "en"


class SignalOut(BaseModel):
    id: str
    symbol: str
    direction: Literal["long", "short", "neutral"]
    thesis: str
    risk_reward: dict[str, Any]
    key_levels: dict[str, Any]
    catalysts: list[str]
    confidence: float
    audit_record_id: str
    disclaimers: list[str]


# ---- Reports ---------------------------------------------------------------
class ReportRequest(BaseModel):
    kind: Literal["deep_dive", "portfolio_analysis", "client_report", "memo"]
    subject_type: Literal["asset", "portfolio", "watchlist"]
    subject_id: str
    language: Language = "en"


class ReportOut(BaseModel):
    id: str
    kind: str
    subject_type: str
    subject_id: str
    language: str
    status: Literal["queued", "generating", "ready", "failed"]
    content: dict[str, Any] | None = None
    audit_record_id: str | None = None


# ---- Alerts ----------------------------------------------------------------
class AlertOut(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    severity: Literal["info", "material", "critical"]
    message: str
    read: bool


# ---- Watchlists ------------------------------------------------------------
class WatchlistCreate(BaseModel):
    name: str
    symbols: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class WatchlistOut(BaseModel):
    id: str
    name: str
    asset_ids: list[str]
    rules: dict[str, Any]


# ---- Webhooks --------------------------------------------------------------
class WebhookCreate(BaseModel):
    url: str
    events: list[str] = Field(default_factory=lambda: ["alert.raised"])


class WebhookOut(BaseModel):
    id: str
    url: str
    events: list[str]
    active: bool


# The analyze/deep-dive endpoints return the Envelope directly.
AnalysisResponse = Envelope
