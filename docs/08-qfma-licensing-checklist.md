# 8. QFMA Licensing Checklist

A working, engineering-and-operations checklist for pursuing a **Qatar Financial
Markets Authority (QFMA)** pathway for an **information & advisory** service.

> **IMPORTANT — not legal advice.** QFMA rules, license categories, capital
> requirements, and fees change and must be confirmed with qualified Qatari
> counsel and directly with QFMA. Items marked _[confirm with counsel]_ need
> authoritative sourcing before you rely on them. This document is the internal
> checklist the platform is engineered to satisfy, not a statement of the law.

## 8.1 Scope & positioning

- [ ] Confirm the activity classification with QFMA: financial **advisory /
      research / information services**, explicitly **excluding** custody,
      dealing/execution, and asset management. _[confirm with counsel]_
- [ ] Confirm whether a QFMA license (vs. QFC/QFCRA route) applies to the chosen
      legal entity and activity, and which regime governs. _[confirm]_
- [ ] Document that the platform performs **no execution and holds no client
      assets** at launch (reduces license scope and capital).
- [ ] Confirm treatment of **cross-border**/online delivery to Qatari residents
      and the marketing rules that apply. _[confirm]_

## 8.2 Entity, governance & people

- [ ] Establish the Qatari legal entity / branch as required for the license.
- [ ] Meet minimum **capital / financial resources** requirement for the
      category. _[confirm amount]_
- [ ] Appoint fit-and-proper senior management; identify **controlled functions**
      (e.g. compliance officer, MLRO). _[confirm titles/requirements]_
- [ ] Board & governance framework, org chart, and reporting lines documented.
- [ ] Professional indemnity insurance appropriate to advisory activity. _[confirm]_

## 8.3 Conduct, disclosures & suitability

- [ ] Prominent **disclaimers** on every client-facing surface: not guaranteed,
      not personalized advice unless licensed + segmented (EN **and** AR,
      reviewed translations). → implemented in `guardrails.py` / reporting.
- [ ] **Client segmentation** (retail / professional / eligible counterparty)
      captured and used to gate advice-style language. → `User.segmentation`.
- [ ] **Suitability & appropriateness** checks where personalized advice is
      offered; risk-profiling on onboarding. → `SUITABILITY`, risk profile.
- [ ] No "buy/sell" personalized recommendations unless licensed for it and the
      user is appropriately segmented. → `NO_ADVICE_UNLESS_SEGMENTED`.
- [ ] Clear fees/charges disclosure and conflicts-of-interest policy. _[confirm]_
- [ ] Financial promotions / marketing approved and compliant. _[confirm]_

## 8.4 Product restrictions (enforced in-platform)

- [ ] **No crypto** anywhere. → `NO_CRYPTO` at ingest + output re-check.
- [ ] **No leveraged / margin products.** → `NO_LEVERAGE` at ingest + output.
- [ ] Only permitted asset classes covered (equity, ETF, bond, fund, FX, macro).
- [ ] Speculative / forward-looking content explicitly marked. → `MARK_SPECULATIVE`.

## 8.5 Data, records & auditability

- [ ] **Data residency:** Qatari client data storable/processable in-region.
      → region-parameterized infra; `Organization.data_region`.
- [ ] **Full auditability:** every AI output traceable to input sources +
      timestamps, model/versions, assumptions/parameters, and compliance
      outcomes. → immutable `AuditRecord`; `GET /v1/audit/{id}`.
- [ ] **Never mutate source data;** corrections stored as new versions.
      → append-only raw stores.
- [ ] **Records retention** per QFMA requirements (retention period, format,
      export). _[confirm period]_
- [ ] Client agreements, communications, and recommendations retained + retrievable.

## 8.6 AML / CFT & KYC

- [ ] AML/CFT program aligned to Qatar (QFMA/QFIU) requirements: risk
      assessment, KYC/CDD, screening, suspicious-transaction reporting. _[confirm]_
- [ ] Appoint MLRO; staff AML training. _[confirm]_
- [ ] KYC-lite at onboarding now; full KYC where/when required by activity/license.

## 8.7 Security & operational resilience

- [ ] Information security program toward **SOC 2 / ISO 27001**: encryption at
      rest/in transit, RBAC, least-privilege IAM, secrets management, audit logs.
- [ ] Business continuity / disaster recovery plan; incident response.
- [ ] Third-party/data-provider due diligence and contractual data rights
      (entitlements enforced in retrieval). → `ENTITLEMENT`.
- [ ] Outsourcing/cloud governance acceptable to QFMA (AWS region, controls). _[confirm]_

## 8.8 Ongoing obligations (post-license)

- [ ] Periodic regulatory reporting and returns. _[confirm cadence]_
- [ ] Complaints handling procedure and register.
- [ ] Change-notification obligations (controllers, senior staff, activities).
- [ ] Annual compliance review + external audit as required. _[confirm]_
- [ ] Compliance sign-off gate at every product release (see roadmap).

## 8.9 Mapping: platform controls → checklist

| Requirement | Where it lives |
|-------------|----------------|
| No crypto / no leverage | `services/data/policy.py` + guardrail re-check |
| Disclaimers (EN/AR) | `services/ai/guardrails.py`, reporting agent |
| Advice gating by segmentation | `User.segmentation`, `guardrails._may_give_advice` |
| Audit trail per output | `core/audit.py`, `GET /v1/audit/{id}` |
| No raw mutation | `repository/memory.py` (append-only) |
| Data residency | region-parameterized infra, `Organization.data_region` |
| Entitlements | RAG retrieval scoping (`services/ai/rag.py`) |

**Next actions:** engage Qatari counsel to resolve every _[confirm]_ item,
obtain the authoritative QFMA rulebook references, and turn this checklist into a
tracked licensing project plan with owners and dates.
