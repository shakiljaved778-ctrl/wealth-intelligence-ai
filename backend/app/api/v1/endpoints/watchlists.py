"""Watchlists + monitoring.

Create/list watchlists, add assets, and run the monitoring agent to detect
material changes (news/filings/price moves) and raise alerts — dispatching any
registered `alert.raised` webhooks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import Principal, get_principal
from app.models import Alert, Watchlist
from app.repository import repo
from app.schemas.api import AlertOut, WatchlistCreate, WatchlistOut
from app.services import notifications
from app.services.ai.agents import MonitoringAgent
from app.services.ai.rag import retriever

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _owned(watchlist_id: str, principal: Principal) -> Watchlist:
    wl = repo.watchlists.get(watchlist_id)
    if not wl or wl.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "watchlist not found")
    return wl


def _to_out(wl: Watchlist) -> WatchlistOut:
    return WatchlistOut(id=wl.id, name=wl.name, asset_ids=wl.asset_ids, rules=wl.rules)


@router.get("", response_model=list[WatchlistOut])
async def list_watchlists(principal: Principal = Depends(get_principal)) -> list[WatchlistOut]:
    return [_to_out(w) for w in repo.watchlists.values() if w.organization_id == principal.org_id]


@router.post("", response_model=WatchlistOut, status_code=201)
async def create_watchlist(body: WatchlistCreate, principal: Principal = Depends(get_principal)) -> WatchlistOut:
    asset_ids = [a.id for s in body.symbols if (a := repo.asset_by_symbol(s))]
    wl = Watchlist(
        organization_id=principal.org_id,
        name=body.name,
        asset_ids=asset_ids,
        rules=body.rules or {"news_filings": True, "price_move_pct": 5.0},
    )
    repo.add_watchlist(wl)
    return _to_out(wl)


@router.post("/{watchlist_id}/assets", response_model=WatchlistOut)
async def add_assets(
    watchlist_id: str, symbols: list[str], principal: Principal = Depends(get_principal)
) -> WatchlistOut:
    wl = _owned(watchlist_id, principal)
    for s in symbols:
        asset = repo.asset_by_symbol(s)
        if asset and asset.id not in wl.asset_ids:
            wl.asset_ids.append(asset.id)
    return _to_out(wl)


@router.post("/{watchlist_id}/scan", response_model=list[AlertOut])
async def scan(watchlist_id: str, principal: Principal = Depends(get_principal)) -> list[AlertOut]:
    """Run the monitoring agent over the watchlist; raise + return alerts."""
    wl = _owned(watchlist_id, principal)
    agent = MonitoringAgent()
    raised: list[AlertOut] = []
    for asset_id in wl.asset_ids:
        asset = repo.assets.get(asset_id)
        if not asset:
            continue
        evidence = retriever.retrieve(asset_symbol=asset.symbol)
        severity = agent.assess_materiality(evidence)
        if severity == "info":
            continue
        alert = Alert(
            organization_id=principal.org_id,
            user_id=principal.actor if principal.kind == "user" else None,
            subject_type="asset",
            subject_id=asset.id,
            severity=severity,  # type: ignore[arg-type]
            message=f"Material update detected for {asset.symbol}: " + (evidence[0].text if evidence else ""),
            trigger={"watchlist_id": wl.id, "rule": "news_filings"},
        )
        repo.add_alert(alert)
        # Fan out to any registered alert.raised webhooks (STUB delivery).
        alert.delivered_channels = notifications.dispatch(
            principal.org_id, "alert.raised", {"alert_id": alert.id, "symbol": asset.symbol}
        )
        raised.append(
            AlertOut(
                id=alert.id,
                subject_type=alert.subject_type,
                subject_id=alert.subject_id,
                severity=alert.severity,
                message=alert.message,
                read=False,
            )
        )
    return raised
