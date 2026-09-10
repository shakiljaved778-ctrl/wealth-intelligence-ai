"""Usage / metering + plan limits (per seat, per call)."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends

from app.api.deps import Principal, get_principal
from app.core.config import settings
from app.repository import repo

router = APIRouter(prefix="/usage", tags=["usage"])

_TIER_LIMITS = {
    "starter": {"calls_per_month": 5_000, "seats": 3, "rate_limit_per_min": 60},
    "professional": {"calls_per_month": 100_000, "seats": 25, "rate_limit_per_min": 240},
    "enterprise": {"calls_per_month": 5_000_000, "seats": 1_000, "rate_limit_per_min": 1_200},
}


@router.get("")
async def usage(principal: Principal = Depends(get_principal)) -> dict:
    records = [u for u in repo.usage if u.organization_id == principal.org_id]
    by_endpoint = Counter(u.endpoint for u in records)
    return {
        "organization_id": principal.org_id,
        "total_calls": len(records),
        "by_endpoint": dict(by_endpoint),
    }


@router.get("/limits")
async def limits(principal: Principal = Depends(get_principal)) -> dict:
    org = repo.organizations.get(principal.org_id)
    tier = org.tier if org else "starter"
    return {
        "tier": tier,
        "limits": _TIER_LIMITS.get(tier, _TIER_LIMITS["starter"]),
        "default_rate_limit_per_min": settings.default_rate_limit_per_min,
    }
