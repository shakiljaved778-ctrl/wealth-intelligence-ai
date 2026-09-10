"""Portfolios: CRUD + risk/AI analysis + construction/rebalance suggestions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import Principal, get_principal, meter, rate_limit
from app.api.v1.endpoints._guard import guard_ctx
from app.models import Portfolio, Position
from app.repository import repo
from app.schemas.api import AnalyzeRequest, ConstructRequest, PortfolioCreate, PortfolioOut
from app.schemas.envelope import Envelope
from app.services.ai import engine
from app.services.ai.agents import PortfolioAgent

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


def _owned(portfolio_id: str, principal: Principal) -> Portfolio:
    pf = repo.portfolios.get(portfolio_id)
    if not pf or pf.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "portfolio not found")
    return pf


def _to_out(pf: Portfolio) -> PortfolioOut:
    return PortfolioOut(
        id=pf.id,
        name=pf.name,
        base_currency=pf.base_currency,
        kind=pf.kind,
        constraints=pf.constraints,
        positions=[{"asset_id": p.asset_id, "quantity": p.quantity} for p in pf.positions],
    )


@router.get("", response_model=list[PortfolioOut])
async def list_portfolios(principal: Principal = Depends(get_principal)) -> list[PortfolioOut]:
    return [_to_out(p) for p in repo.portfolios.values() if p.organization_id == principal.org_id]


@router.post("", response_model=PortfolioOut, status_code=201)
async def create_portfolio(body: PortfolioCreate, principal: Principal = Depends(get_principal)) -> PortfolioOut:
    positions: list[Position] = []
    for p in body.positions:
        asset = repo.asset_by_symbol(p.symbol)
        if not asset:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown symbol {p.symbol}")
        positions.append(Position(asset_id=asset.id, quantity=p.quantity))
    pf = Portfolio(
        organization_id=principal.org_id,
        name=body.name,
        base_currency=body.base_currency,
        kind=body.kind,
        constraints=body.constraints,
        positions=positions,
    )
    repo.add_portfolio(pf)
    return _to_out(pf)


@router.get("/{portfolio_id}", response_model=PortfolioOut)
async def get_portfolio(portfolio_id: str, principal: Principal = Depends(get_principal)) -> PortfolioOut:
    return _to_out(_owned(portfolio_id, principal))


@router.post("/{portfolio_id}/analyze", response_model=Envelope)
async def analyze(
    portfolio_id: str,
    body: AnalyzeRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    _rl: None = Depends(rate_limit),
    _m: None = Depends(meter),
) -> Envelope:
    pf = _owned(portfolio_id, principal)
    ctx = guard_ctx(principal, request, body.language)
    scenarios = [s.model_dump() for s in body.scenarios]
    return engine.analyze_portfolio(portfolio=pf, gctx=ctx, scenarios=scenarios)


@router.post("/construct", response_model=Envelope)
async def construct(
    body: ConstructRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    _rl: None = Depends(rate_limit),
    _m: None = Depends(meter),
) -> Envelope:
    """Model-portfolio construction under constraints (suggestions only)."""
    if body.universe:
        assets = [a for s in body.universe if (a := repo.asset_by_symbol(s))]
    else:
        assets = list(repo.assets.values())
    if not assets:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no valid assets in universe")
    ctx = guard_ctx(principal, request, body.language)
    return engine.construct_portfolio(
        assets=assets,
        risk_profile=body.risk_profile,
        max_position_weight=body.max_position_weight,
        gctx=ctx,
    )


@router.post("/{portfolio_id}/rebalance")
async def rebalance(
    portfolio_id: str, targets: dict[str, float], principal: Principal = Depends(get_principal)
) -> dict:
    """Rebalance SUGGESTIONS only — no execution at launch."""
    pf = _owned(portfolio_id, principal)
    total_mv = 0.0
    current: dict[str, float] = {}
    for pos in pf.positions:
        asset = repo.assets.get(pos.asset_id)
        bars = repo.latest_prices(pos.asset_id, limit=1) if asset else []
        if not bars:
            continue
        mv = pos.quantity * bars[-1].close
        current[asset.symbol] = mv  # type: ignore[union-attr]
        total_mv += mv
    current = {k: (v / total_mv if total_mv else 0.0) for k, v in current.items()}
    deltas = PortfolioAgent().rebalance_suggestions(current, targets)
    return {
        "current_weights": current,
        "target_weights": targets,
        "suggested_deltas": deltas,
        "note": "suggestions only; no execution",
    }
