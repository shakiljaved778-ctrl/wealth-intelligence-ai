"""Immutable audit records — the spine of explainability.

Every AI output writes exactly one AuditRecord capturing inputs, models,
assumptions, parameters, compliance outcomes, and confidence. Records are
append-only: there is intentionally no update or delete API.
See docs/05-compliance.md §5.4.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: "aud_" + uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    org_id: str
    actor: str  # user id or api_key id
    request_id: str
    language: str = "en"

    inputs: list[dict[str, Any]] = Field(default_factory=list)  # observed source ids + timestamps
    derived: list[dict[str, Any]] = Field(default_factory=list)  # metrics used (methodology/params)
    models: list[dict[str, str]] = Field(default_factory=list)  # [{name, version}]
    assumptions: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    compliance: list[dict[str, Any]] = Field(default_factory=list)  # rule evaluations
    confidence: dict[str, Any] = Field(default_factory=dict)


class AuditStore:
    """Append-only store. Backed by an immutable table / WORM storage in prod."""

    def __init__(self) -> None:
        self._records: dict[str, AuditRecord] = {}

    def write(self, record: AuditRecord) -> AuditRecord:
        if record.id in self._records:
            raise RuntimeError("audit records are immutable; id already exists")
        self._records[record.id] = record
        return record

    def get(self, record_id: str, *, org_id: str) -> AuditRecord | None:
        rec = self._records.get(record_id)
        if rec is None or rec.org_id != org_id:
            return None
        return rec


audit_store = AuditStore()
