# 6. Roadmap (MVP → V1 → V2)

Milestones are outcome-based. Dates are indicative; each phase ends with a
compliance review because the product is regulated.

## MVP — months 0–4  ("prove the spine")

**Goal:** end-to-end, single-language, with the observed/derived/narrative
discipline real from day one.

- **Data ingestion:** connectors for 1–2 market-data + 1 fundamentals provider;
  canonical schema; append-only raw store; `NO_CRYPTO`/`NO_LEVERAGE` ingest filter.
- **Analytics:** basic portfolio analytics — weights, concentration, simple
  factor exposure, basic drawdown.
- **AI:** simple asset deep-dive memos + portfolio read (RAG + one LLM), full
  guardrail layer + audit records.
- **B2B API (alpha):** auth (JWT + API keys), assets, portfolios,
  `/analyze`, `/deep-dive`, usage metering; OpenAPI published.
- **B2C web app (alpha):** onboarding (risk profiling), dashboard, asset
  deep-dive, model portfolios (static), **EN only**.
- **Platform:** AWS multi-AZ, structured logging/tracing, RBAC, encryption,
  CI/CD.

**Exit criteria:** a portfolio analysis returns a correct 3-layer envelope with
a retrievable audit record; disclaimers present; no raw mutation path exists.

## V1 — months 4–9  ("full analytics, Arabic, monetize")

- **Risk analytics:** complete factor attribution, stress testing, scenario
  analysis (rates/oil/FX/inflation), VaR/drawdown suite.
- **Trading signals:** signal generation with thesis/risk-reward/levels/
  catalysts; watchlist monitoring + alerts (news/filings/price) with webhooks.
- **Arabic:** full EN/AR UI + generation with the bilingual glossary; approved
  AR disclaimers; RTL.
- **B2B billing:** tiers (Starter/Professional/Enterprise), per-seat + per-call
  metering, rate limits, SLAs.
- **Compliance workflows:** suitability + concentration checks, segmentation
  gating, audit export.
- **Behavioral coaching:** bias detection surfaced in advisory flows.

**Exit criteria:** paying B2B tenant live; AR reports shippable; alerts firing
on material events; billing reconciles to usage records.

## V2 — months 9–18+  ("agentic depth, integrations, expansion")

- **Advanced agents:** richer multi-step research/portfolio/monitoring graphs;
  scenario engine with configurable macro shock libraries.
- **Broker integrations:** execution *adapters* (still advisory by default;
  execution only where separately licensed) via a clean adapter interface —
  designed for since MVP.
- **Jurisdiction expansion:** beyond Qatar; per-region residency + entitlement;
  localized compliance rule packs.
- **Enterprise:** SSO, private deployments, model/version pinning per tenant,
  SOC 2 / ISO 27001 certification.
- **B2C growth:** freemium → subscription funnel, richer personalization within
  the segmentation/licensing guardrails.

## Cross-cutting, every phase

- Compliance sign-off gate at each release.
- Audit coverage never regresses (every AI output stays traceable).
- The "no raw mutation / no crypto / no leverage" invariants are tested in CI.
