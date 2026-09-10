# 3. B2B API Specification (OpenAPI-style summary)

Base URL: `https://api.wealthintelligence.ai/v1` · Content type: `application/json`

The live, browsable OpenAPI schema is served by the FastAPI app at `/openapi.json`
and `/docs`. This document is the human-readable summary of the contract.

## 3.1 Conventions

- **Auth:** `Authorization: Bearer <JWT>` for user/session flows;
  `X-API-Key: <key>` for server-to-server. Scopes enforced per key.
- **Versioning:** URI-versioned (`/v1`).
- **Errors:** RFC 7807 problem+json (`type`, `title`, `status`, `detail`,
  `instance`).
- **Rate limiting:** `X-RateLimit-Limit` / `-Remaining` / `-Reset` headers;
  `429` on exceed. Metered per seat and per call.
- **Idempotency:** mutating POSTs accept `Idempotency-Key`.
- **Async:** long jobs (reports) return `202` + a resource you poll or a webhook.
- **Every analytical response** carries the `observed` / `derived` / `narrative`
  envelope and an `audit_record_id`.

## 3.2 Endpoints

### Auth
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/token` | OAuth2 password/client-credentials → access + refresh JWT |
| `POST` | `/auth/refresh` | Exchange refresh token for new access token |
| `POST` | `/auth/api-keys` | (admin) mint a server-to-server API key with scopes |
| `DELETE` | `/auth/api-keys/{id}` | Revoke an API key |

`POST /auth/token` → `{ access_token, refresh_token, token_type, expires_in, scope }`

### Assets
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/assets` | Search/lookup assets (`q`, `asset_class`, `country`, paging) |
| `GET` | `/assets/{id}` | Asset facts (identifiers, class, currency, sector) |
| `GET` | `/assets/{id}/prices` | Raw OHLCV (`interval`, `from`, `to`) — **observed only** |
| `GET` | `/assets/{id}/fundamentals` | Raw fundamentals snapshots — **observed only** |
| `POST` | `/assets/{id}/deep-dive` | AI deep-dive memo (observed+derived+narrative) |

`POST /assets/{id}/deep-dive` req: `{ language?, sections?, portfolio_context? }`
→ 3-layer envelope with `narrative` sections (summary, fundamentals read,
risks, scenarios, signal view) + `audit_record_id`.

### Portfolios
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/portfolios` | List portfolios for org |
| `POST` | `/portfolios` | Create portfolio (`name`, `base_currency`, `constraints`, positions) |
| `GET` | `/portfolios/{id}` | Portfolio detail + positions |
| `PATCH` | `/portfolios/{id}` | Update constraints/metadata |
| `POST` | `/portfolios/{id}/analyze` | **Risk + AI analysis** (concentration, factor exposure, downside/stress + narrative) |
| `POST` | `/portfolios/{id}/construct` | Model-portfolio construction / optimization under constraints |
| `POST` | `/portfolios/{id}/rebalance` | Rebalance suggestions vs targets (suggestions only — no execution) |

`POST /portfolios/{id}/analyze` req: `{ scenarios?: [...], language?, benchmarks?: [...] }`
→ `observed` (positions, prices), `derived` (concentration, factor exposures,
VaR/drawdown/stress results), `narrative` (plain-language risk read),
`audit_record_id`.

### Signals
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/signals` | List signals (`asset_id?`, `status?`, `horizon?`) |
| `POST` | `/signals/generate` | Generate signal(s) for an asset/universe |
| `GET` | `/signals/{id}` | Signal detail (thesis, risk/reward, levels, catalysts) |

`POST /signals/generate` req: `{ asset_id | universe, horizon, constraints? }`
→ signal with `direction`, `thesis` (narrative), `risk_reward`, `key_levels`,
`catalysts`, `confidence`, `audit_record_id`.

### Reports
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/reports` | Request async report (`kind`, `subject`, `language` EN/AR) → `202` |
| `GET` | `/reports/{id}` | Poll status / fetch content when `ready` |
| `GET` | `/reports` | List reports for org |

`POST /reports` req: `{ kind: "client_report"|"deep_dive"|"portfolio_analysis",
subject_type, subject_id, language: "en"|"ar" }` → `202 { id, status: "queued" }`.
Completion also fires a webhook (`report.ready`).

### Alerts & Watchlists
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/alerts` | List alerts (`severity?`, `unread?`) |
| `POST` | `/alerts/{id}/read` | Mark alert read |
| `GET` | `/watchlists` / `POST` `/watchlists` | Manage watchlists |
| `POST` | `/watchlists/{id}/assets` | Add assets to a monitored watchlist |
| `POST` | `/alerts/rules` | Define alert rules (news/filings/price/signal thresholds) |

Monitoring agents ingest news/filings/market moves for watchlist assets and
raise alerts when something **material** changes; delivery via webhook + in-app.

### Webhooks
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks` | Register endpoint + events (`report.ready`, `alert.raised`, `signal.updated`) |
| `GET` | `/webhooks` | List registrations |
| `DELETE` | `/webhooks/{id}` | Remove |

Payloads are signed (`X-WIA-Signature`, HMAC-SHA256) and retried with backoff.

### Usage / Metering
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/usage` | Current period usage (per seat, per call, per endpoint) |
| `GET` | `/usage/limits` | Plan limits + rate-limit config for the org |

### Audit
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/audit/{audit_record_id}` | Full provenance for an AI output (inputs, models, assumptions, compliance) |

## 3.3 GraphQL (optional)

A read-optimized GraphQL endpoint at `/graphql` can be layered later for
clients that need to co-fetch an asset with its prices, fundamentals, factor
exposures, and latest signal in one round trip. REST remains the contract of
record; GraphQL is a convenience projection over the same services and the
same guardrail layer (so the 3-layer envelope and audit records still apply).
