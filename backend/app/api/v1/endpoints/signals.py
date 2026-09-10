"""Trading signals: generation + retrieval (idea + rationale, not execution)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import Principal, get_principal, meter, rate_limit
from app.api.v1.endpoints._guard import guard_ctx
from app.models import Signal
from app.repository import repo
from app.schemas.api import SignalGenerateRequest, SignalOut
from app.services.ai import engine

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalOut])
async def list_signals(symbol: str | None = None, principal: Principal = Depends(get_principal)) -> list[SignalOut]:
    out = []
    for sig in repo.signals.values():
        asset = repo.assets.get(sig.asset_id)
        if not asset:
            continue
        if symbol and asset.symbol.upper() != symbol.upper():
            continue
        out.append(_to_out(sig, asset.symbol))
    return out


def _to_out(sig: Signal, symbol: str) -> SignalOut:
    return SignalOut(
        id=sig.id,
        symbol=symbol,
        direction=sig.direction,
        thesis=sig.thesis,
        risk_reward=sig.risk_reward,
        key_levels=sig.key_levels,
        catalysts=sig.catalysts,
        confidence=sig.confidence,
        audit_record_id=sig.audit_record_id or "",
        disclaimers=[],
    )


@router.post("/generate", response_model=SignalOut)
async def generate(
    body: SignalGenerateRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    _rl: None = Depends(rate_limit),
    _m: None = Depends(meter),
) -> SignalOut:
    asset = repo.asset_by_symbol(body.symbol)
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "asset not found")
    ctx = guard_ctx(principal, request, body.language)
    result = engine.generate_signal(asset=asset, horizon=body.horizon, gctx=ctx)
    sig = Signal(
        asset_id=asset.id,
        direction=result["direction"],
        thesis=result["thesis"],
        risk_reward=result["risk_reward"],
        key_levels=result["key_levels"],
        catalysts=result["catalysts"],
        horizon=body.horizon,
        confidence=result["confidence"],
        audit_record_id=result["audit_record_id"],
    )
    repo.add_signal(sig)
    out = _to_out(sig, asset.symbol)
    out.disclaimers = result["disclaimers"]
    return out
