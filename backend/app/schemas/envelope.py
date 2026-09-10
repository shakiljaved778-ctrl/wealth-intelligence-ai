"""The three-layer response envelope — the platform's core invariant.

Every analytical response separates:
  * observed  — provider facts (never mutated; source + as_of)
  * derived   — platform-computed metrics (methodology + params + model version)
  * narrative — AI interpretation (cited; marked interpretation vs scenario)

Making the split a *type* (not a prompt instruction) is what keeps
"raw vs derived vs narrative" structural. See docs/02-data-model.md §2.3.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Observed(BaseModel):
    field: str
    value: Any
    source: str
    as_of: datetime
    unit: str | None = None


class Derived(BaseModel):
    metric: str
    value: Any
    methodology: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    model_version: str
    confidence: float | None = None


class Narrative(BaseModel):
    text: str
    # Citations reference observed/derived items, e.g. "obs:price.close" / "der:concentration_hhi".
    citations: list[str] = Field(default_factory=list)
    kind: Literal["interpretation", "scenario"] = "interpretation"
    speculative: bool = False
    section: str | None = None  # e.g. "summary", "risks", "fundamentals"


class Envelope(BaseModel):
    """Attributed, compliance-checked analytical payload."""

    observed: list[Observed] = Field(default_factory=list)
    derived: list[Derived] = Field(default_factory=list)
    narrative: list[Narrative] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    language: str = "en"
    audit_record_id: str | None = None
