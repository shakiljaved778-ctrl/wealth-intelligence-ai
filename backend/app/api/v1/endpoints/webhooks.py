"""Webhooks: register endpoints for async events (alerts, reports, signals)."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Principal, get_principal
from app.models import Webhook
from app.repository import repo
from app.schemas.api import WebhookCreate, WebhookOut

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookOut, status_code=201)
async def register(body: WebhookCreate, principal: Principal = Depends(get_principal)) -> WebhookOut:
    wh = Webhook(
        organization_id=principal.org_id,
        url=body.url,
        events=body.events,
        secret=secrets.token_urlsafe(24),
    )
    repo.add_webhook(wh)
    return WebhookOut(id=wh.id, url=wh.url, events=wh.events, active=wh.active)


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(principal: Principal = Depends(get_principal)) -> list[WebhookOut]:
    return [
        WebhookOut(id=w.id, url=w.url, events=w.events, active=w.active)
        for w in repo.webhooks.values()
        if w.organization_id == principal.org_id
    ]


@router.delete("/{webhook_id}", status_code=204)
async def remove(webhook_id: str, principal: Principal = Depends(get_principal)) -> None:
    wh = repo.webhooks.get(webhook_id)
    if not wh or wh.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "webhook not found")
    wh.active = False
