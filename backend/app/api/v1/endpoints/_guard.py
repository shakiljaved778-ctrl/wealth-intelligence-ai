"""Build a GuardrailContext from an authenticated Principal + request."""

from __future__ import annotations

from fastapi import Request

from app.api.deps import Principal
from app.core.logging import request_id_var
from app.services.ai.guardrails import GuardrailContext


def guard_ctx(principal: Principal, request: Request, language: str | None = None) -> GuardrailContext:
    return GuardrailContext(
        org_id=principal.org_id,
        actor=principal.actor,
        request_id=request_id_var.get(),
        language=language or principal.language,
        licensed_for_advice=principal.licensed_for_advice,
        user_segmentation=principal.segmentation,
    )
