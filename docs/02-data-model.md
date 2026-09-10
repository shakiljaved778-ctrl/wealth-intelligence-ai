# 2. Data Model (Conceptual)

Core entities, key fields, and relationships. This is deliberately
provider-agnostic and expressed clearly enough to generate DDL / ORM models
later. The Python/Pydantic mirrors live in
[`backend/app/schemas/`](../backend/app/schemas) and the domain entities in
[`backend/app/models/`](../backend/app/models).

## 2.1 Entity relationship overview

```
Organization 1───* User
Organization 1───* Portfolio
Organization 1───* ApiKey
Organization 1───* ComplianceRule (+ global defaults)

Asset 1───* PriceBar
Asset 1───* FundamentalSnapshot
Asset 1───* FactorExposure
Asset 1───* Signal

Portfolio 1───* Position *───1 Asset
Portfolio 1───* Report
Portfolio 1───* Alert
User      1───* Alert
Watchlist *───* Asset            (a User/Org may hold Watchlists)

Every AI-produced entity (Signal, Report, and analysis payloads)
1───1 AuditRecord   (inputs, model versions, assumptions, timestamps)
```

## 2.2 Entities

### Organization
Tenant / customer (a bank, broker, fintech, or the B2C operator itself).
- `id`, `name`, `type` (`bank|broker|prop|fintech|b2c`)
- `data_region` (e.g. `qa`, `eu`, `global`) — drives residency
- `tier` (`starter|professional|enterprise`)
- `licensing_context` — whether personalized advice is permitted for this tenant
- `created_at`

### User
- `id`, `organization_id` (FK), `email`, `role` (`admin|analyst|advisor|client|viewer`)
- `locale` (`en|ar`), `risk_profile` (see below), `investment_objectives`
- `segmentation` — `retail|professional|eligible_counterparty` (gates advice language)
- `created_at`, `last_login_at`

### Asset
Canonical instrument. **Facts only.**
- `id`, `symbol`, `isin`, `figi`, `name`
- `asset_class` (`equity|etf|bond|fund|fx|macro`) — **excludes crypto & leveraged products by construction**
- `exchange`, `currency`, `country`, `sector`, `industry`
- `is_tradable_policy_ok` (bool) — set false/ingest-blocked for disallowed instruments
- `metadata` (jsonb)

### PriceBar
Immutable OHLCV time series. **Never mutated.**
- `asset_id` (FK), `interval` (`1m|5m|1h|1d`), `ts`
- `open`, `high`, `low`, `close`, `volume`
- `source`, `ingested_at`, `version` — corrections append a new version

### FundamentalSnapshot
Point-in-time fundamentals. **Never mutated.**
- `asset_id` (FK), `as_of`, `period` (`Q|A`)
- `statements` (jsonb: income/balance/cashflow), `estimates` (jsonb)
- `ratios` (jsonb — *raw* provider ratios, distinct from derived scores)
- `source`, `ingested_at`, `version`

### FactorExposure  *(derived)*
- `asset_id` (FK), `as_of`
- `factors` (jsonb: `{value, growth, momentum, quality, size, volatility, ...}`)
- `methodology`, `model_version`, `computed_at`

### Portfolio
- `id`, `organization_id` (FK), `owner_user_id` (FK, nullable for model portfolios)
- `name`, `base_currency`, `kind` (`model|client|custom`)
- `constraints` (jsonb: max position %, sector caps, exclusions, factor targets)
- `created_at`, `updated_at`

### Position
- `portfolio_id` (FK), `asset_id` (FK)
- `quantity`, `weight` (derived-on-read or stored), `cost_basis`, `as_of`

### Signal  *(derived + narrative)*
- `id`, `asset_id` (FK), `created_at`, `status` (`active|triggered|closed|expired`)
- `direction` (`long|short|neutral`) — *short* used for hedging/analysis, not leverage
- `thesis` (narrative), `risk_reward` (jsonb: target, stop, rr_ratio)
- `key_levels` (jsonb), `catalysts` (jsonb array), `horizon`
- `confidence`, `audit_record_id` (FK)

### Report  *(narrative, may embed derived + observed)*
- `id`, `organization_id` (FK), `subject_type` (`asset|portfolio|watchlist`), `subject_id`
- `kind` (`deep_dive|portfolio_analysis|client_report|memo`)
- `language` (`en|ar`), `status` (`queued|generating|ready|failed`)
- `content` (structured sections), `audit_record_id` (FK)
- `created_at`, `ready_at`

### Alert
- `id`, `organization_id` (FK), `user_id` (FK, nullable), `subject_type`, `subject_id`
- `trigger` (jsonb: rule that fired), `severity` (`info|material|critical`)
- `message`, `delivered_channels` (jsonb), `created_at`, `read_at`

### ComplianceRule
- `id`, `organization_id` (FK, nullable = global default)
- `code` (e.g. `NO_CRYPTO`, `NO_LEVERAGE`, `NO_ADVICE_UNLESS_SEGMENTED`, `CONCENTRATION_LIMIT`)
- `params` (jsonb), `severity` (`block|warn`), `enabled`

### AuditRecord  *(immutable)*
The spine of explainability. One per AI output.
- `id`, `created_at`
- `inputs` (jsonb: data source ids + timestamps used)
- `models` (jsonb: `[{name, version}]`)
- `assumptions` (jsonb), `parameters` (jsonb)
- `compliance` (jsonb: rules evaluated + outcomes)
- `confidence` / `uncertainty` (jsonb)

### ApiKey / UsageRecord  *(metering)*
- `ApiKey`: `id`, `organization_id`, `hashed_key`, `scopes`, `rate_limit`, `revoked`
- `UsageRecord`: `organization_id`, `api_key_id`, `endpoint`, `units`, `ts` (per-seat / per-call metering)

## 2.3 The three-layer envelope (response contract)

Every analytical response is shaped as:

```jsonc
{
  "observed":  [ { "field": "...", "value": ..., "source": "...", "as_of": "..." } ],
  "derived":   [ { "metric": "...", "value": ..., "methodology": "...",
                   "parameters": {...}, "model_version": "..." } ],
  "narrative": [ { "text": "...", "citations": ["obs:...", "der:..."],
                   "kind": "interpretation|scenario", "speculative": bool } ],
  "audit_record_id": "..."
}
```

This contract is the single most important invariant: it makes the
observed/derived/narrative separation *structural*, not stylistic.
