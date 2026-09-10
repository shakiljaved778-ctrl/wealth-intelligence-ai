"""Shared API dependencies: authentication, rate limiting, usage metering."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import decode_token, hash_api_key
from app.models import UsageRecord
from app.repository import repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/token", auto_error=False)


@dataclass
class Principal:
    """The authenticated caller (a user via JWT or a service via API key)."""

    org_id: str
    actor: str  # user id or api key id
    scopes: list[str]
    kind: str  # "user" | "api_key"
    segmentation: str = "retail"
    licensed_for_advice: bool = False
    language: str = "en"


async def get_principal(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Principal:
    # Server-to-server: API key
    if x_api_key:
        key = repo.api_key_by_hash(hash_api_key(x_api_key))
        if not key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
        org = repo.organizations.get(key.organization_id)
        return Principal(
            org_id=key.organization_id,
            actor=key.id,
            scopes=key.scopes,
            kind="api_key",
            licensed_for_advice=bool(org and org.licensing_context.get("advice", False)),
        )
    # User/session: JWT
    if token:
        try:
            claims = decode_token(token)
        except ValueError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from None
        if claims.get("kind") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not an access token")
        user = repo.users.get(claims["sub"])
        org = repo.organizations.get(claims["org"])
        return Principal(
            org_id=claims["org"],
            actor=claims["sub"],
            scopes=claims.get("scopes", []),
            kind="user",
            segmentation=user.segmentation if user else "retail",
            licensed_for_advice=bool(org and org.licensing_context.get("advice", False)),
            language=user.locale if user else "en",
        )
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing credentials")


def require_scope(scope: str):
    async def _dep(principal: Principal = Depends(get_principal)) -> Principal:
        if scope not in principal.scopes and "admin" not in principal.scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"missing scope '{scope}'")
        return principal

    return _dep


# ---- rate limiting (in-process token buckets; use Redis in prod) ----------
_buckets: dict[str, list[float]] = defaultdict(list)


async def rate_limit(request: Request, principal: Principal = Depends(get_principal)) -> None:
    now = time.time()
    window = 60.0
    bucket = _buckets[principal.actor]
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= settings.default_rate_limit_per_min:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "rate limit exceeded")
    bucket.append(now)


# ---- usage metering (per seat / per call) ---------------------------------
async def meter(request: Request, principal: Principal = Depends(get_principal)) -> None:
    repo.record_usage(
        UsageRecord(
            organization_id=principal.org_id,
            api_key_id=principal.actor if principal.kind == "api_key" else None,
            user_id=principal.actor if principal.kind == "user" else None,
            endpoint=request.url.path,
        )
    )
