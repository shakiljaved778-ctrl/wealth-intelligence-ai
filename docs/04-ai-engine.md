# 4. AI Engine Design

The AI engine turns **observed facts** + **derived metrics** into **cited,
compliant narrative** — never the other way around. Code lives in
[`backend/app/services/ai/`](../backend/app/services/ai).

## 4.1 RAG architecture

**Corpora indexed:**
- Regulatory filings & disclosures (per asset/issuer)
- News & press releases (timestamped)
- Sell-side / internal research notes (where licensed)
- Macro & economic releases
- The platform's own **derived** artifacts (factor exposures, risk metrics) so
  narratives can cite the numbers they explain
- Methodology docs (so the model can explain *how* a score is computed)

**Chunking & indexing:**
- Documents are chunked semantically (section-aware), each chunk carrying
  metadata: `asset_id`, `issuer_id`, `doc_type`, `published_at`, `source`,
  `language`, `jurisdiction`.
- Embeddings stored in a vector index (e.g. pgvector / OpenSearch / a managed
  vector DB), partitioned by `data_region` for residency.
- Every chunk keeps a stable `citation_id` so retrieved evidence maps 1:1 to
  citations in the output envelope.

**Retrieval scoping:** retrieval is *always* filtered — never a global search:
- by **asset / portfolio** (only evidence about the subject or its holdings)
- by **recency** (respect the analysis `as_of`; don't leak future info into a
  historical view)
- by **language** (prefer EN or AR corpora per request, fall back with a note)
- by **entitlement** (a tenant only retrieves corpora it's licensed for)
- by **region** (residency partition)

**Grounding rule:** the generation step receives *only* retrieved evidence plus
the computed derived metrics. Any narrative sentence must map to at least one
citation; the guardrail layer drops uncited factual claims.

## 4.2 Agent framework

Orchestrated with **LangGraph** (stateful graphs) over **LlamaIndex** retrievers;
each agent is a node with typed inputs/outputs and a shared, audited context.

| Agent | Responsibility | Produces |
|-------|---------------|----------|
| **Research agent** | Asset/issuer deep-dives: gather fundamentals, filings, news; synthesize | deep-dive sections + citations |
| **Portfolio agent** | Construction, optimization, rebalancing suggestions under constraints | target weights + rationale (suggestions only) |
| **Risk agent** | Coordinate the quant core (factor/concentration/stress) and explain results | derived metrics + plain-language read |
| **Signal agent** | Idea generation: thesis, risk/reward, key levels, catalysts, monitoring | `Signal` objects |
| **Monitoring agent** | Watch news/filings/price for watchlists; detect materiality; raise alerts | `Alert` objects |
| **Reporting agent** | Assemble client-ready reports in EN/AR from the above | `Report` objects |
| **Compliance agent** | Final pass: applies rules, strips/annotates disallowed content | pass/fail + annotations |

Agents never call data providers directly for *facts they then assert* — they
consume the canonical feature store and the quant core, so provenance is always
attributable.

## 4.3 Derived metrics: computed and logged separately from raw data

- Derived metrics (risk scores, factor attributions, fair-value estimates,
  scenario outputs) are computed in the **deterministic quant core**
  ([`backend/app/services/risk/analytics.py`](../backend/app/services/risk/analytics.py))
  or specialized models — **never** by free-form LLM arithmetic.
- Each derived value is stored with `methodology`, `parameters`, `model_version`,
  and `computed_at`, and lands in the feature store — a *different* store from
  raw facts. The LLM may *explain* a derived number but may not *change* it.
- In responses, derived values live in the `derived` array, distinct from
  `observed`. See the envelope contract in [`docs/02-data-model.md`](02-data-model.md).

## 4.4 Compliance rule enforcement

Enforced by the **guardrail layer + compliance agent**, driven by
`ComplianceRule` records:
- **Structural:** the response envelope forces the observed/derived/narrative
  split; uncited factual narrative is rejected.
- **Content rules:**
  - `NO_CRYPTO` / `NO_LEVERAGE` — enforced at ingestion (data never enters) and
    re-checked at output.
  - `NO_ADVICE_UNLESS_SEGMENTED` — personalized "buy/sell" language is replaced
    with neutral, educational phrasing unless the tenant is licensed *and* the
    user is segmented appropriately.
  - `MARK_SPECULATIVE` — scenario/forecast content is tagged `speculative: true`
    and rendered with a disclaimer.
  - `CONCENTRATION_LIMIT`, suitability checks — evaluated against portfolio/user.
- Every evaluation (rule, outcome, transformation) is written to the
  `AuditRecord`. See [`backend/app/services/ai/guardrails.py`](../backend/app/services/ai/guardrails.py).

## 4.5 Multilingual (EN / AR)

**Approach: multilingual-capable generation + a controlled terminology layer**
(not naive post-hoc machine translation), because financial/regulatory terms
must be exact and Arabic is RTL.

- Retrieval prefers corpora in the requested language; cross-language evidence
  is allowed but the fact that a source was translated is noted.
- Generation is done directly in the target language by a multilingual model,
  constrained by a **bilingual financial glossary** (EN↔AR canonical terms) so
  regulated terminology stays consistent.
- Numbers, tickers, and dates are locale-formatted; Arabic renders RTL with
  correct numeral policy.
- Disclaimers and compliance annotations have reviewed, approved translations —
  never generated ad hoc.
- The audit record stores the language and glossary version used.

## 4.6 Confidence & uncertainty

Where a derived metric or narrative rests on estimates, the engine attaches a
confidence/uncertainty indicator (e.g. dispersion of estimates, data
completeness, model calibration) to the `derived`/`narrative` items and the
audit record — so downstream UIs can show it and never imply false precision.
