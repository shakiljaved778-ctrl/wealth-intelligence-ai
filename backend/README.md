# Backend — Wealth Intelligence AI

FastAPI service: the B2B API, the AI engine, and the deterministic risk/quant
core. The scaffold runs with an **in-memory repository** and **deterministic
stubs** for data providers and the LLM, so it starts with no external
dependencies and demonstrates the full request → guardrail → audit flow.

## Run

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
# → http://localhost:8000/docs   (OpenAPI UI)
```

Seed demo data is loaded on startup (a couple of assets + a demo portfolio and
org). A demo bearer token is printed at startup for local exploration.

## Layout

```
app/
├── main.py                  # app factory, middleware, router mount, seed
├── core/
│   ├── config.py            # WIA_* settings
│   ├── security.py          # JWT + API-key auth
│   ├── logging.py           # structured logging + request_id
│   └── audit.py             # AuditRecord writer (immutable)
├── api/
│   ├── deps.py              # auth / rate-limit / metering dependencies
│   └── v1/
│       ├── router.py
│       └── endpoints/       # auth, assets, portfolios, signals, reports, alerts, usage, audit
├── schemas/                 # Pydantic request/response models (incl. 3-layer envelope)
├── models/                  # domain entities
├── repository/              # in-memory store (swap for SQLAlchemy later)
└── services/
    ├── data/                # provider connectors + canonical normalization (STUB)
    ├── risk/                # deterministic quant core (derived metrics)
    └── ai/                  # RAG, agents, guardrails, engine (narrative)
```

## Where the invariants live

- **No raw mutation:** `repository/` exposes no update/delete for `PriceBar` /
  `FundamentalSnapshot`; corrections append a new version.
- **3-layer envelope:** `schemas/envelope.py` — the response contract.
- **Guardrails + audit:** `services/ai/guardrails.py`, `core/audit.py`.
- **No crypto / no leverage:** `services/data/policy.py` (ingest filter) and
  re-checked in guardrails.

## Tests

```bash
pytest -q
```
