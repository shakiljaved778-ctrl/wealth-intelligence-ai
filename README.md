# Wealth Intelligence AI

> AI-powered B2B2C wealth banking & intelligence platform — advisory, portfolio
> construction, risk analytics, and trading signals across global finance
> products, **without ever altering source data**.

Wealth Intelligence AI augments existing market/fundamental/alternative data
with transparent, explainable intelligence. The platform is **information &
advisory only** at launch (no custody, no execution, no crypto, no leverage) and
is designed for a **QFMA-first, global-ready** regulatory path.

The one rule everything else is built around:

> **The AI never changes, hides, or fabricates factual data.** If NVIDIA's
> 1-year performance is X, it stays X. AI may *explain*, *contextualize*,
> *derive transparent metrics*, *run scenarios*, and *generate narratives* —
> each labelled and sourced.

Every AI output is separated into three layers, enforced in code:

| Layer | What it is | Guarantee |
|-------|-----------|-----------|
| **Observed** | Facts from data providers | Never mutated; always carries source + timestamp |
| **Derived** | Scores, risk metrics, fair-value estimates | Methodology + parameters exposed; logged separately |
| **Narrative** | AI-generated explanations | Cited, marked as interpretation, compliance-checked |

## Repository layout

```
wealth-intelligence-ai/
├── docs/            # Architecture, data model, API spec, AI engine, compliance, roadmap
├── backend/         # FastAPI service (Python) — API + AI engine + risk analytics
├── frontend/        # Next.js + React (TypeScript) B2C web app, EN/AR
├── infra/           # AWS / deployment notes and IaC stubs
├── docker-compose.yml
└── Makefile
```

## The seven design deliverables (from the product brief)

1. [Architecture](docs/01-architecture.md)
2. [Data model](docs/02-data-model.md)
3. [B2B API specification](docs/03-api-spec.md)
4. [AI engine design](docs/04-ai-engine.md)
5. Implementation scaffolding — see [`backend/`](backend/) and [`frontend/`](frontend/)
6. [Compliance & guardrails blueprint](docs/05-compliance.md)
7. [Roadmap (MVP → V1 → V2)](docs/06-roadmap.md)

## Quick start (dev)

```bash
# Backend
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload      # http://localhost:8000/docs

# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev                        # http://localhost:3000

# Or everything at once
docker compose up --build
```

## Status

This repository is an **implementation-ready scaffold**: the architecture,
contracts, and guardrail machinery are real and coherent; data connectors and
model calls are wired as clearly-marked stubs (`# STUB:`) so the system runs
end-to-end with deterministic mock data and can be filled in provider-by-provider.

## Non-negotiables (encoded in the platform)

- No crypto. No leveraged products. Enforced at the data layer *and* product layer.
- No overwriting of raw provider data — ever.
- Every factual statement carries a source and timestamp.
- Speculative / scenario content is explicitly marked.
- No personalized "buy/sell" language unless the user is segmented and the
  deployment is appropriately licensed.
- Every AI recommendation is auditable to its inputs, model versions, and assumptions.

See [`docs/05-compliance.md`](docs/05-compliance.md) for the full blueprint.
