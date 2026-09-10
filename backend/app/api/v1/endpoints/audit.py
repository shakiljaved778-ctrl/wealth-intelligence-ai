"""Audit: full provenance for any AI output (scoped to the owning org)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Principal, get_principal
from app.core.audit import AuditRecord, audit_store

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{audit_record_id}", response_model=AuditRecord)
async def get_audit(audit_record_id: str, principal: Principal = Depends(get_principal)) -> AuditRecord:
    rec = audit_store.get(audit_record_id, org_id=principal.org_id)
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "audit record not found")
    return rec
