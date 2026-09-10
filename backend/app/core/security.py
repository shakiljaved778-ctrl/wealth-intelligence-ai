"""Authentication primitives: JWT (OAuth2) and hashed API keys.

Two credential types (see docs/03-api-spec.md §3.1):
  * JWT bearer tokens  — user/session flows
  * API keys           — server-to-server (B2B), hashed at rest, scoped
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

# Password hashing: stdlib PBKDF2-HMAC-SHA256 (salted, iterated). Chosen over
# bcrypt to keep the scaffold dependency-light and avoid version-coupled native
# builds. A production deployment may swap in argon2/bcrypt behind these two
# functions without changing callers.
_PBKDF2_ITERATIONS = 240_000


# ---- Passwords -------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        scheme, iterations, salt_hex, dk_hex = hashed.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


# ---- JWT -------------------------------------------------------------------
def create_token(subject: str, *, scopes: list[str], org_id: str, kind: str = "access") -> str:
    now = datetime.now(UTC)
    minutes = settings.access_token_expire_minutes if kind == "access" else settings.refresh_token_expire_minutes
    claims: dict[str, Any] = {
        "sub": subject,
        "org": org_id,
        "scopes": scopes,
        "kind": kind,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:  # pragma: no cover - thin wrapper
        raise ValueError("invalid token") from exc


# ---- API keys --------------------------------------------------------------
def generate_api_key() -> tuple[str, str]:
    """Return ``(plaintext, sha256_hash)``. Only the hash is stored."""
    plaintext = "wia_" + secrets.token_urlsafe(32)
    return plaintext, hash_api_key(plaintext)


def hash_api_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()
