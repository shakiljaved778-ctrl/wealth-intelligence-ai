# 7. Pitch Deck Outline

A 14-slide investor/partner deck for Wealth Intelligence AI. Each slide lists
its **purpose**, the **key message**, and **content to show**. Speaker notes are
in italics. This is an outline to build from (deck tool of choice) — not final
copy. Figures marked _[assumption]_ are placeholders to replace with validated
numbers.

> Positioning throughout: **information & advisory only** at launch — no custody,
> no execution, no crypto, no leverage. QFMA-first, global-ready. The wedge is
> **transparent, auditable AI that never alters source data.**

---

### Slide 1 — Title / one-liner
- **Purpose:** frame the company in one breath.
- **Message:** "AI-powered wealth intelligence for banks and investors —
  explainable, auditable, and Qatar-first."
- **Show:** logo, tagline, presenter, date, confidentiality note.

### Slide 2 — The problem
- **Message:** Advisory and research are expensive, slow, and inconsistent;
  existing "AI" tools hallucinate, hide sources, and can't be audited — a
  non-starter in regulated wealth management.
- **Show:** 3 pain points (cost/scale, trust/explainability, compliance risk);
  a stat on advisor coverage gaps _[assumption]_.
- *Regulators and risk teams block black-box AI; that's the real adoption
  barrier we remove.*

### Slide 3 — The insight / why now
- **Message:** LLMs + RAG finally make explainable, cited financial narrative
  possible — but only if the architecture *separates fact from interpretation*.
  Rising MENA wealth + Qatar's fintech push create the opening.
- **Show:** the observed → derived → narrative separation as the "why now"
  technical unlock; market timing (regional wealth growth, QFMA modernization).

### Slide 4 — The product
- **Message:** One platform: portfolio construction, risk analytics, trading
  signals, and AI advisory — B2B API + B2C app, English & Arabic.
- **Show:** product screenshot (the three-layer EnvelopeView), the 5 core
  capabilities as icons.

### Slide 5 — The differentiator (the moat)
- **Message:** **We never change source data.** Every AI output is split into
  observed (facts + source + timestamp), derived (metrics + methodology), and
  narrative (cited interpretation) — with a full audit trail per output.
- **Show:** side-by-side "black-box AI" vs "Wealth Intelligence AI" (sourced,
  audited, compliance-checked). This is the slide investors remember.

### Slide 6 — How it works (architecture, simplified)
- **Message:** Data in (never mutated) → deterministic quant core → AI engine
  (RAG + agents) → guardrail + audit → API/app.
- **Show:** the simplified architecture diagram from `docs/01-architecture.md`;
  emphasize the guardrail/audit chokepoint.

### Slide 7 — Compliance as a feature
- **Message:** Built for regulators: no crypto/leverage, disclaimers everywhere,
  advice gated by licensing + user segmentation, Qatar data residency, full
  auditability.
- **Show:** the compliance rule table (subset) and "auditable to inputs, models,
  assumptions" line. *This is what closes B2B deals.*

### Slide 8 — Market
- **Message:** B2B first (banks, brokers, prop/trading firms, fintechs), B2C
  second (investors). Qatar/GCC beachhead → global.
- **Show:** TAM/SAM/SOM _[assumption]_; beachhead logos/targets; expansion map.

### Slide 9 — Business model
- **Message:** B2B: per-seat + per-API-call + enterprise (Starter/Professional/
  Enterprise tiers, SLAs). B2C: freemium → subscription.
- **Show:** pricing tiers table; unit economics sketch _[assumption]_;
  metering/usage is already built in.

### Slide 10 — Traction / status
- **Message:** Working platform scaffold (API + app + AI engine + guardrails +
  CI), running end-to-end; pilots/LOIs in progress _[assumption]_.
- **Show:** what's live vs next; any design partners; a demo QR/link.

### Slide 11 — Go-to-market
- **Message:** Land via a Qatar bank/broker design partner → QFMA licensing
  pathway → regional expansion; B2C funnel piggybacks on B2B credibility.
- **Show:** GTM motion timeline; partner pipeline; regulatory milestones.

### Slide 12 — Roadmap
- **Message:** MVP (core analytics + memos, EN) → V1 (full risk, signals,
  Arabic, billing, compliance workflows) → V2 (agents, scenario engine, broker
  integrations, new jurisdictions).
- **Show:** the 3-phase roadmap from `docs/06-roadmap.md` on a timeline.

### Slide 13 — Team & advisors
- **Message:** Why this team wins (fintech + AI + regional/regulatory).
- **Show:** founders, key hires, advisors (regulatory/QFMA, banking) _[fill in]_.

### Slide 14 — Ask
- **Message:** Raising **$[X]** to reach [milestones: licensing, first N B2B
  tenants, V1] over [N] months.
- **Show:** use of funds (eng, data/licensing, compliance, GTM), key milestones,
  contact. _[assumption — set with the financial model]_

---

**Appendix slides (optional):** detailed architecture, security/SOC2 posture,
sample audit record, competitive matrix, financial model summary, QFMA licensing
checklist (see `docs/08-qfma-licensing-checklist.md`).
