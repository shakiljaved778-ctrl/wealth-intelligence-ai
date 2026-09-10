# CLAUDE.md

Guidance for working in this repository.

## What this is

Wealth Intelligence AI — a B2B2C wealth banking & AI intelligence platform
(advisory, portfolio construction, risk analytics, trading signals). It augments
market/fundamental/alternative data with transparent, explainable intelligence.
Information & advisory only: **no custody, no execution, no crypto, no leverage.**

## Non-negotiable invariants (do not break these)

1. **Never mutate raw facts.** `PriceBar` / `FundamentalSnapshot` are append-only;
   corrections are new versions. The repository intentionally exposes no
   update/delete for them (`backend/app/repository/memory.py`).
2. **Three-layer envelope.** Every analytical response separates `observed`
   (facts + source + timestamp), `derived` (metrics + methodology + model
   version), `narrative` (cited AI interpretation). It's a type, not a prompt:
   `backend/app/schemas/envelope.py`.
3. **Guardrails + audit.** Every AI output goes through
   `backend/app/services/ai/guardrails.py` (rejects uncited factual narrative,
   neutralizes unlicensed advice language, marks speculative content, attaches
   disclaimers) and writes one immutable `AuditRecord` (`core/audit.py`).
4. **No crypto / no leverage.** Enforced at ingest (`services/data/policy.py`)
   and re-checked at output.
5. **Derived metrics are computed deterministically** in `services/risk/`, never
   by free-form LLM arithmetic. The LLM explains numbers; it never changes them.

These are covered by tests in `backend/tests/test_invariants.py` and
`test_api.py` — keep them green.

## Layout

- `docs/` — architecture, data model, API spec, AI engine, compliance, roadmap.
- `backend/` — FastAPI: `api/v1/endpoints/` (routers), `schemas/`, `models/`,
  `repository/` (in-memory; swap for SQLAlchemy), `services/{data,risk,ai}`.
- `frontend/` — Next.js + TS, EN/AR (RTL). `lib/api.ts`, `components/EnvelopeView.tsx`.
- `infra/` — AWS notes, region-parameterized for Qatar residency.

## Commands

Backend (needs a venv — the base image's Debian `cryptography` conflicts):
```bash
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
ruff check app tests && ruff format --check app tests && pytest -q
uvicorn app.main:app --reload      # /docs; startup prints a demo token
```
Frontend:
```bash
cd frontend && npm install && npx tsc --noEmit && npm run build && npm run dev
```

CI (`.github/workflows/ci.yml`) runs both on every push/PR. A SessionStart hook
(`.claude/hooks/session-start.sh`) installs both dependency sets for web sessions.

## Conventions

- Stubs (data providers, LLM, webhook delivery) are marked `# STUB:` — real
  implementations drop in behind them without changing callers.
- The scaffold runs fully offline: in-memory repository + deterministic stubs.
- Keep new analytical endpoints returning the `Envelope` and writing an audit
  record via the guardrail layer.
