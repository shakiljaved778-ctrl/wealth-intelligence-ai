"""Webhook dispatch.

Signs payloads (HMAC-SHA256) and would POST them to registered endpoints. In
this scaffold delivery is a STUB: we compute the signature and record the
attempt rather than making outbound calls to arbitrary URLs. Swap the STUB for
an async HTTP client with retries/backoff in production.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from app.core.logging import get_logger
from app.repository import repo

log = get_logger(__name__)


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def dispatch(org_id: str, event: str, payload: dict[str, Any]) -> list[str]:
    """Deliver `event` to all matching webhooks. Returns the ids notified."""
    body = json.dumps({"event": event, "data": payload}, default=str).encode()
    notified: list[str] = []
    for wh in repo.webhooks_for_event(org_id, event):
        signature = sign(wh.secret, body)
        # STUB: real impl -> httpx.post(wh.url, content=body,
        #                                headers={"X-WIA-Signature": signature})
        log.info(
            "webhook dispatch (stub)",
            extra={"extra_fields": {"webhook_id": wh.id, "event": event, "signature": signature[:12]}},
        )
        notified.append(wh.id)
    return notified
