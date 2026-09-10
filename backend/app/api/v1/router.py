"""Mounts all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    assets,
    audit,
    auth,
    portfolios,
    reports,
    signals,
    usage,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(assets.router)
api_router.include_router(portfolios.router)
api_router.include_router(signals.router)
api_router.include_router(reports.router)
api_router.include_router(alerts.router)
api_router.include_router(usage.router)
api_router.include_router(audit.router)
