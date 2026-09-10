"""Guardrail layer — the response-path chokepoint.

Every analytical payload passes through here before leaving the API. It:
  * enforces the observed / derived / narrative split (structural);
  * rejects narrative factual claims that lack a citation;
  * applies compliance rules (no crypto/leverage; no personalized advice unless
    licensed + segmented; mark speculative; disclaimers);
  * writes exactly one immutable AuditRecord.

See docs/05-compliance.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.audit import AuditRecord, audit_store
from app.core.config import settings
from app.schemas.envelope import Envelope, Narrative

# Language that implies a personalized recommendation to buy/sell.
_ADVICE_PATTERNS = re.compile(
    r"\b(you should (buy|sell)|we recommend (buying|selling)|(buy|sell) now|strong buy|strong sell)\b",
    re.IGNORECASE,
)

DISCLAIMER_EN = (
    "Information and analysis for educational purposes only; not personalized "
    "investment advice, not guaranteed. No crypto or leveraged products. "
    "Forward-looking scenarios are speculative."
)
DISCLAIMER_AR = (
    "معلومات وتحليلات لأغراض تعليمية فقط؛ ليست نصيحة استثمارية مخصصة وغير مضمونة. "
    "لا تشمل العملات المشفرة أو المنتجات ذات الرافعة المالية. السيناريوهات المستقبلية تقديرية."
)


@dataclass
class GuardrailContext:
    org_id: str
    actor: str
    request_id: str
    language: str = "en"
    licensed_for_advice: bool = False
    user_segmentation: str = "retail"
    models: list[dict[str, str]] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)


class ComplianceViolation(Exception):
    pass


def _may_give_advice(ctx: GuardrailContext) -> bool:
    return (
        settings.allow_personalized_advice
        and ctx.licensed_for_advice
        and ctx.user_segmentation in ("professional", "eligible_counterparty")
    )


def apply(envelope: Envelope, ctx: GuardrailContext) -> Envelope:
    """Validate + sanitize an envelope and attach its audit record."""
    compliance_log: list[dict] = []

    valid_citations = {f"obs:{o.field}" for o in envelope.observed}
    valid_citations |= {f"der:{d.metric}" for d in envelope.derived}
    # Evidence citations (doc:...) are also permitted.
    sanitized: list[Narrative] = []

    for n in envelope.narrative:
        text = n.text

        # 1) Uncited factual interpretation is not allowed to ship.
        if n.kind == "interpretation" and not n.citations:
            compliance_log.append(
                {
                    "code": "SOURCE_AND_TIMESTAMP",
                    "outcome": "block",
                    "detail": "uncited narrative dropped",
                }
            )
            continue
        bad = [c for c in n.citations if not c.startswith("doc:") and c not in valid_citations]
        if bad:
            compliance_log.append(
                {
                    "code": "SOURCE_AND_TIMESTAMP",
                    "outcome": "block",
                    "detail": f"invalid citations {bad} dropped",
                }
            )
            continue

        # 2) No personalized buy/sell language unless licensed + segmented.
        if _ADVICE_PATTERNS.search(text) and not _may_give_advice(ctx):
            text = _ADVICE_PATTERNS.sub("[educational: consider discussing with a licensed advisor]", text)
            compliance_log.append(
                {
                    "code": "NO_ADVICE_UNLESS_SEGMENTED",
                    "outcome": "rewrite",
                    "detail": "advice language neutralized",
                }
            )

        # 3) Scenario/forward-looking content must be marked speculative.
        if n.kind == "scenario":
            n.speculative = True
            compliance_log.append({"code": "MARK_SPECULATIVE", "outcome": "annotate", "detail": n.section})

        sanitized.append(Narrative(**{**n.model_dump(), "text": text}))

    envelope.narrative = sanitized

    # 4) Re-check no crypto / no leverage at the output boundary (defence in depth).
    blob = " ".join(o.field.lower() + " " + str(o.value).lower() for o in envelope.observed)
    for banned, code in (("crypto", "NO_CRYPTO"), ("leverage", "NO_LEVERAGE")):
        if banned in blob:
            raise ComplianceViolation(code)
    compliance_log.append({"code": "NO_CRYPTO", "outcome": "pass"})
    compliance_log.append({"code": "NO_LEVERAGE", "outcome": "pass"})

    # 5) Disclaimers are mandatory on every client-facing analytical output.
    envelope.disclaimers = [DISCLAIMER_AR if ctx.language == "ar" else DISCLAIMER_EN]
    compliance_log.append({"code": "DISCLAIMER_REQUIRED", "outcome": "pass"})

    # 6) Write the immutable audit record.
    record = AuditRecord(
        org_id=ctx.org_id,
        actor=ctx.actor,
        request_id=ctx.request_id,
        language=ctx.language,
        inputs=[o.model_dump(mode="json") for o in envelope.observed],
        derived=[
            {
                "metric": d.metric,
                "methodology": d.methodology,
                "parameters": d.parameters,
                "model_version": d.model_version,
            }
            for d in envelope.derived
        ],
        models=ctx.models,
        assumptions=ctx.assumptions,
        parameters=ctx.parameters,
        compliance=compliance_log,
    )
    audit_store.write(record)
    envelope.audit_record_id = record.id
    envelope.language = ctx.language
    return envelope
