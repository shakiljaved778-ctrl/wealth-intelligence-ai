"""Auth endpoints: OAuth2 token, refresh, and API-key management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import Principal, require_scope
from app.core.config import settings
from app.core.security import create_token, decode_token, generate_api_key, verify_password
from app.models import ApiKey
from app.repository import repo
from app.schemas.api import ApiKeyCreate, ApiKeyCreated, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = repo.user_by_email(form.username)
    if not user or not user.hashed_password or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    scopes = form.scopes or ["read", "write"]
    return TokenResponse(
        access_token=create_token(user.id, scopes=scopes, org_id=user.organization_id, kind="access"),
        refresh_token=create_token(user.id, scopes=scopes, org_id=user.organization_id, kind="refresh"),
        expires_in=settings.access_token_expire_minutes * 60,
        scope=" ".join(scopes),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    try:
        claims = decode_token(body.refresh_token)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token") from None
    if claims.get("kind") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not a refresh token")
    scopes = claims.get("scopes", ["read"])
    return TokenResponse(
        access_token=create_token(claims["sub"], scopes=scopes, org_id=claims["org"], kind="access"),
        refresh_token=create_token(claims["sub"], scopes=scopes, org_id=claims["org"], kind="refresh"),
        expires_in=settings.access_token_expire_minutes * 60,
        scope=" ".join(scopes),
    )


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(body: ApiKeyCreate, principal: Principal = Depends(require_scope("admin"))) -> ApiKeyCreated:
    plaintext, hashed = generate_api_key()
    key = ApiKey(
        organization_id=principal.org_id,
        name=body.name,
        hashed_key=hashed,
        scopes=body.scopes,
        rate_limit_per_min=settings.default_rate_limit_per_min,
    )
    repo.add_api_key(key)
    # Plaintext is returned once, at creation, and never stored.
    return ApiKeyCreated(id=key.id, api_key=plaintext, scopes=key.scopes)


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(key_id: str, principal: Principal = Depends(require_scope("admin"))) -> None:
    key = repo.api_keys.get(key_id)
    if not key or key.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    key.revoked = True
