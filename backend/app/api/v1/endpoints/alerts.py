"""Alerts & watchlist monitoring."""

from __future__ import annotations

from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Principal, get_principal
from app.repository import repo
from app.schemas.api import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(unread: bool = False, principal: Principal = Depends(get_principal)) -> list[AlertOut]:
    out = []
    for a in repo.alerts.values():
        if a.organization_id != principal.org_id:
            continue
        if unread and a.read_at is not None:
            continue
        out.append(
            AlertOut(
                id=a.id,
                subject_type=a.subject_type,
                subject_id=a.subject_id,
                severity=a.severity,
                message=a.message,
                read=a.read_at is not None,
            )
        )
    return out


@router.post("/{alert_id}/read", status_code=204)
async def mark_read(alert_id: str, principal: Principal = Depends(get_principal)) -> None:
    from datetime import datetime

    alert = repo.alerts.get(alert_id)
    if not alert or alert.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "alert not found")
    alert.read_at = datetime.now(UTC)
