# 1. High-Level Architecture

> **Assumption:** AWS is the target cloud. Qatar-region data residency is a
> first-class constraint — components that touch Qatari client data are designed
> to be pinned to an in-region deployment (e.g. `me-central-1` / a QFMA-approved
> local zone) via the same IaC with a region variable.

## 1.1 Component map (text diagram)

```
                            EXTERNAL DATA PROVIDERS
        ┌──────────────┬───────────────┬────────────────┬──────────────┐
        │ Market data  │ Fundamentals  │ Filings/News   │ Alt data     │
        │ (eq/etf/bond │ (statements,  │ (regulatory,   │ (sentiment,  │
        │  fund/fx/    │  estimates,   │  corporate     │  ESG, macro, │
        │  macro)      │  actions)     │  actions)      │  geopolitics)│
        └──────┬───────┴───────┬───────┴───────┬────────┴──────┬───────┘
               │               │               │               │
        ╔══════▼═══════════════▼═══════════════▼═══════════════▼══════╗
        ║  INGESTION LAYER  (connectors → normalization → validation) ║
        ║  • per-provider adapters   • canonical schema mapping       ║
        ║  • "no crypto / no leverage" filter applied HERE            ║
        ║  • immutability guard: raw records are append-only          ║
        ╚══════╤═══════════════════════════════════╤══════════════════╝
               │ (raw, immutable, timestamped)     │
        ┌──────▼───────────┐              ┌────────▼─────────┐
        │  DATA LAKE (S3)  │              │  WAREHOUSE       │  raw layer
        │  raw events,     │◄────────────►│  (Postgres/      │  ← FACTS ONLY
        │  filings, docs   │              │   Redshift)      │
        └──────┬───────────┘              └────────┬─────────┘
               │                                   │
        ┌──────▼───────────────────────────────────▼─────────┐
        │  FEATURE STORE (time-series features)               │  derived layer
        │  asset / portfolio / factor features, versioned     │  ← DERIVED
        └──────┬───────────────────────────────────┬─────────┘
               │                                   │
   ┌───────────▼─────────┐          ┌──────────────▼──────────────────┐
   │  RISK / QUANT CORE  │          │        AI ENGINE                │
   │  • factor attrib.   │          │  • LLM + RAG over docs/news     │
   │  • concentration    │◄────────►│  • specialized models:          │
   │  • drawdown/stress  │  derived │      risk-score, factor-attrib, │
   │  • scenario sim.    │  metrics │      scenario-sim, signal-gen   │
   │  (deterministic)    │          │  • agent framework (LangGraph)  │
   └───────────┬─────────┘          └──────────────┬──────────────────┘
               │                                   │ (narrative + derived)
               │        ╔══════════════════════════▼══════════════════╗
               └───────►║  EXPLANATION & GUARDRAIL LAYER              ║
                        ║  • enforces raw vs derived vs narrative     ║
                        ║  • attaches citations (source + timestamp)  ║
                        ║  • applies compliance rules (no advice/     ║
                        ║    buy-sell unless licensed+segmented)      ║
                        ║  • writes AUDIT RECORD for every output     ║
                        ╚══════════════════════════╤══════════════════╝
                                                   │ (safe, attributed payloads)
        ╔══════════════════════════════════════════▼══════════════════╗
        ║  API LAYER  (FastAPI)                                        ║
        ║  REST (+ optional GraphQL)  • OAuth2/JWT + API keys          ║
        ║  rate limiting • usage metering • webhooks                   ║
        ╚═══════╤═══════════════════════════════════════════╤══════════╝
                │                                           │
     ┌──────────▼───────────┐                   ┌───────────▼──────────┐
     │  B2C WEB APP         │                   │  B2B API CONSUMERS   │
     │  Next.js + React     │                   │  banks, brokers,     │
     │  EN/AR, dashboards   │                   │  fintechs (S2S)      │
     └──────────────────────┘                   └──────────────────────┘

        CROSS-CUTTING:  Auth/RBAC · Audit log (immutable) · Observability
        (structured logs, tracing, metrics) · Secrets (KMS) · Encryption
        at rest & in transit · Compliance policy engine
```

## 1.2 Where "raw vs derived vs narrative" separation is enforced

The separation is enforced at **three chokepoints**, not just by convention:

1. **Ingestion (write path):** raw provider records land in an *append-only*
   store. There is no `UPDATE`/`DELETE` API path for raw market/fundamental
   facts. Corrections from a provider are stored as *new* versions with their
   own timestamp; the original is retained.
2. **AI engine (compute path):** derived metrics are computed in the
   risk/quant core or specialized models and always carry a
   `methodology` + `parameters` + `model_version`. They are stored in the
   feature store, *never* written back over raw facts.
3. **Guardrail layer (read/response path):** every payload leaving the API is a
   typed envelope with three explicit sections (`observed`, `derived`,
   `narrative`). The guardrail layer rejects any narrative claim that lacks a
   citation and any response that violates a compliance rule, and it emits an
   immutable audit record. See [`backend/app/services/ai/guardrails.py`](../backend/app/services/ai/guardrails.py).

## 1.3 Data flow (request example: "analyze this portfolio")

1. Client calls `POST /v1/portfolios/{id}/analyze` (JWT or API key).
2. API resolves the portfolio's positions → pulls **raw** prices/fundamentals
   (facts, with source + `as_of`).
3. Risk/quant core computes **derived** metrics (concentration, factor
   exposures, stress results) with exposed methodology.
4. AI engine (RAG + agents) generates **narrative** insights, each citing the
   raw/derived items it used.
5. Guardrail layer assembles the 3-layer envelope, runs compliance checks,
   writes the audit record.
6. API returns the attributed response; usage is metered.

## 1.4 Non-functional posture

- **Security:** encryption at rest (KMS) and in transit (TLS 1.2+); RBAC per
  org/user/scope; least-privilege IAM; secrets in AWS Secrets Manager; targeting
  SOC 2 / ISO 27001 controls.
- **Data residency:** region-parameterized IaC; Qatari client data can be pinned
  in-region; per-tenant `data_region` attribute drives storage/routing.
- **Observability:** OpenTelemetry traces, structured JSON logs with
  `request_id`/`org_id`/`model_version`, metrics for latency, error rate, and
  model/token usage.
- **Availability:** multi-AZ; stateless API tier behind a load balancer; async
  work (report generation, monitoring) on a queue (SQS/Celery) with webhooks.

## 1.5 Latency tiers

| Workload | Target | Mechanism |
|----------|--------|-----------|
| Signals & intraday analytics | minutes | streaming/near-real-time feature updates |
| Deep analytics (factor, stress) | EOD acceptable | batch jobs into feature store |
| Report generation | async | queue + webhook / polling on `reports` resource |
