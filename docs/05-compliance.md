# 5. Compliance & Guardrails Blueprint

**Regulatory stance at launch:** information & advisory only — no custody, no
execution, no crypto, no leverage. QFMA (Qatar) licensing pathway first, then
global expansion. Outputs are *not guaranteed* and *not personalized investment
advice* unless the deployment is licensed and the user is appropriately
segmented.

## 5.1 Concrete rules to implement

Each rule has a `code`, `severity` (`block` | `warn`), and is evaluated by the
guardrail layer with the outcome written to the audit record.

| Code | Rule | Severity | Enforced at |
|------|------|----------|-------------|
| `NO_RAW_MUTATION` | Never overwrite raw market/fundamental data; corrections are new versions | block | ingestion (append-only), code review |
| `SOURCE_AND_TIMESTAMP` | Every factual statement carries source + timestamp | block | guardrail (reject uncited facts) |
| `MARK_SPECULATIVE` | Scenario/forecast content explicitly marked + disclaimed | block | guardrail |
| `NO_CRYPTO` | No crypto instruments anywhere | block | ingestion filter + output re-check |
| `NO_LEVERAGE` | No leveraged/leveraged-ETF/margin products | block | ingestion filter + output re-check |
| `NO_ADVICE_UNLESS_SEGMENTED` | No personalized buy/sell language unless licensed + user segmented | block/warn | guardrail (rewrite to neutral) |
| `CONCENTRATION_LIMIT` | Flag/deny suggestions breaching concentration limits | warn/block | portfolio agent + guardrail |
| `SUITABILITY` | Recommendations checked against user risk profile & objectives | warn | compliance agent |
| `DISCLAIMER_REQUIRED` | Every client-facing output carries the approved disclaimer | block | reporting agent |
| `DATA_RESIDENCY` | Qatari client data stored/processed in-region when required | block | infra + routing |
| `ENTITLEMENT` | Tenant only sees corpora/data it is licensed for | block | retrieval scoping |

## 5.2 The three-layer discipline (restated as policy)

- **Observed** = provider facts. Immutable. Always source + `as_of`.
- **Derived** = platform-computed. Methodology + parameters + model version
  exposed. Stored apart from raw.
- **Narrative** = AI interpretation. Cited. Marked interpretation vs scenario.

A response that cannot be decomposed into these three, with citations, does not
ship. This is enforced structurally by the envelope type, not by prompt wording.

## 5.3 Disclaimers (baseline copy, EN)

> *Wealth Intelligence AI provides information and analysis for educational and
> research purposes. It is not personalized investment advice and does not
> constitute an offer or solicitation. Outputs are not guaranteed, may contain
> forward-looking scenarios that are speculative, and should not be the sole
> basis for any decision. No crypto or leveraged products are covered. Consult a
> licensed advisor where appropriate.*

Arabic disclaimer text is a **reviewed, approved translation** stored alongside
the English (never generated ad hoc). Both are versioned.

## 5.4 Audit logging (how decisions are logged)

Every AI output writes one immutable `AuditRecord` containing:
- **Inputs:** the exact data source records + timestamps used (`observed` ids)
- **Derived:** metrics used, with methodology/parameters/model versions
- **Models:** `[{name, version}]` for every model/agent invoked
- **Assumptions & parameters:** scenario shocks, horizons, constraints
- **Compliance:** each rule evaluated and its outcome (pass / warn / block /
  rewritten), including any text transformations applied
- **Confidence/uncertainty:** indicators where relevant
- **Identity:** `org_id`, `user_id`/`api_key_id`, `request_id`, `language`

Audit records are append-only, retained per regulatory requirements, and
retrievable via `GET /v1/audit/{id}` (scoped to the owning org). Structured logs
and traces carry the same `request_id` for reconstruction.

## 5.5 QFMA-first checklist (design-time)

> **Assumption:** exact QFMA obligations are confirmed with counsel; this is the
> engineering-facing checklist the platform is built to satisfy.

- [ ] Information/advisory positioning documented; no custody/execution surface
- [ ] Disclaimers present on every client-facing surface (EN + AR)
- [ ] User segmentation model gating advice language
- [ ] Full auditability (inputs → models → assumptions → output)
- [ ] Data residency: Qatari client data pinnable in-region
- [ ] RBAC, encryption at rest/in transit, secrets management
- [ ] No crypto / no leverage enforced at data + product level
- [ ] Complaint & correction handling (raw corrections as new versions)
- [ ] Records retention & audit export
