# Frontend — Wealth Intelligence AI

Next.js (App Router) + React + TypeScript B2C web app. Bilingual **EN/AR** with
RTL support. Talks to the FastAPI backend and renders the three-layer
(observed / derived / narrative) envelope so users always see *what is a fact,
what is a computed metric, and what is AI interpretation* — with sources.

## Run

```bash
cp .env.example .env.local
npm install
npm run dev          # http://localhost:3000
```

Point `NEXT_PUBLIC_API_BASE_URL` at the backend (default `http://localhost:8000`).
Log in with the demo user (`demo@wealthintelligence.ai` / `demo1234`).

## Pages (App Router)

| Route | Journey |
|-------|---------|
| `/` | Dashboard — portfolio overview, risk metrics, AI insights, watchlists |
| `/assets/[symbol]` | Asset deep-dive — facts, fundamentals, risks, scenarios, signals |
| `/portfolios` | Model portfolios + custom portfolios, analysis |
| `/reports` | Client-ready reports (EN/AR), request + status |
| `/settings` | Locale (EN/AR), risk profile, objectives |

## Key pieces

- `lib/api.ts` — typed API client (auth, assets, portfolios, signals, reports).
- `lib/i18n.ts` — EN/AR dictionary + `dir` (LTR/RTL) helper.
- `components/EnvelopeView.tsx` — renders observed / derived / narrative with
  citations, disclaimers, and speculative markers — the product's signature UI.
