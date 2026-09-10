"""Reports: async generation (EN/AR), status polling, listing.

In this scaffold generation runs inline via a BackgroundTask and the result is
stored on the Report; in production it is a queue worker that also fires the
``report.ready`` webhook.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.api.deps import Principal, get_principal, meter, rate_limit
from app.api.v1.endpoints._guard import guard_ctx
from app.models import Report
from app.repository import repo
from app.schemas.api import ReportOut, ReportRequest
from app.services.ai import engine
from app.services.ai.guardrails import GuardrailContext

router = APIRouter(prefix="/reports", tags=["reports"])


def _run(report_id: str, req: ReportRequest, ctx: GuardrailContext) -> None:
    report = repo.reports.get(report_id)
    if not report:
        return
    report.status = "generating"
    try:
        content = engine.generate_report(
            kind=req.kind, subject_type=req.subject_type, subject_id=req.subject_id, gctx=ctx
        )
        report.content = content
        report.audit_record_id = content.get("audit_record_id")
        report.status = "ready"
        report.ready_at = datetime.now(UTC)
        # STUB: fire `report.ready` webhook here.
    except Exception:  # noqa: BLE001 - record failure, don't crash the worker
        report.status = "failed"


@router.post("", response_model=ReportOut, status_code=202)
async def request_report(
    body: ReportRequest,
    request: Request,
    background: BackgroundTasks,
    principal: Principal = Depends(get_principal),
    _rl: None = Depends(rate_limit),
    _m: None = Depends(meter),
) -> ReportOut:
    report = Report(
        organization_id=principal.org_id,
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        kind=body.kind,
        language=body.language,
        status="queued",
    )
    repo.add_report(report)
    ctx = guard_ctx(principal, request, body.language)
    background.add_task(_run, report.id, body, ctx)
    return ReportOut(**report.model_dump())


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: str, principal: Principal = Depends(get_principal)) -> ReportOut:
    report = repo.reports.get(report_id)
    if not report or report.organization_id != principal.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return ReportOut(**report.model_dump())


@router.get("", response_model=list[ReportOut])
async def list_reports(principal: Principal = Depends(get_principal)) -> list[ReportOut]:
    return [ReportOut(**r.model_dump()) for r in repo.reports.values() if r.organization_id == principal.org_id]
