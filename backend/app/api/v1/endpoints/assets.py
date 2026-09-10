"""Assets: lookup, raw facts (observed only), and AI deep-dive."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import Principal, get_principal, meter, rate_limit
from app.api.v1.endpoints._guard import guard_ctx
from app.repository import repo
from app.schemas.api import AssetOut, DeepDiveRequest
from app.schemas.envelope import Envelope
from app.services.ai import engine

router = APIRouter(prefix="/assets", tags=["assets"])


def _resolve(asset_id: str):
    asset = repo.assets.get(asset_id) or repo.asset_by_symbol(asset_id)
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset not found")
    return asset


@router.get("", response_model=list[AssetOut])
async def search_assets(
    q: str | None = None,
    asset_class: str | None = None,
    _: Principal = Depends(get_principal),
) -> list[AssetOut]:
    return [AssetOut(**a.model_dump()) for a in repo.search_assets(q, asset_class)]


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: str, _: Principal = Depends(get_principal)) -> AssetOut:
    return AssetOut(**_resolve(asset_id).model_dump())


@router.get("/{asset_id}/prices")
async def get_prices(asset_id: str, limit: int = 260, _: Principal = Depends(get_principal)) -> dict:
    """Raw OHLCV — OBSERVED facts only, never derived."""
    asset = _resolve(asset_id)
    bars = repo.latest_prices(asset.id, limit=limit)
    return {
        "symbol": asset.symbol,
        "currency": asset.currency,
        "bars": [b.model_dump(mode="json") for b in bars],
        "note": "observed facts; immutable; corrections appended as new versions",
    }


@router.get("/{asset_id}/fundamentals")
async def get_fundamentals(asset_id: str, _: Principal = Depends(get_principal)) -> dict:
    asset = _resolve(asset_id)
    snap = repo.latest_fundamental(asset.id)
    if not snap:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no fundamentals")
    return {"symbol": asset.symbol, "snapshot": snap.model_dump(mode="json")}


@router.post("/{asset_id}/deep-dive", response_model=Envelope)
async def deep_dive(
    asset_id: str,
    body: DeepDiveRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    _rl: None = Depends(rate_limit),
    _m: None = Depends(meter),
) -> Envelope:
    asset = _resolve(asset_id)
    ctx = guard_ctx(principal, request, body.language)
    return engine.generate_asset_deep_dive(asset=asset, gctx=ctx, sections=body.sections)
