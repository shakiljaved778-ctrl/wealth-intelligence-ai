# Deployment — Vercel (frontend + demo backend)

This document covers deploying the scaffold to **Vercel**. The target production
topology remains AWS multi-AZ with data residency (see
[`infra/README.md`](../infra/README.md) and
[`01-architecture.md`](01-architecture.md)); Vercel is used here for a fast,
shareable preview of the Next.js frontend and — optionally — the FastAPI backend
as a Python serverless function.

> **No secrets in git.** Every value below is set in the Vercel dashboard
> (Project → Settings → Environment Variables) or via `vercel env`. Nothing
> sensitive is committed. The repo ships only `*.env.example` templates.

## Layout

This is a monorepo. Deploy the frontend and backend as **two separate Vercel
projects**, each with its own **Root Directory**:

| Vercel project | Root Directory | Config |
|----------------|----------------|--------|
| `wealth-intelligence-web` | `frontend` | [`frontend/vercel.json`](../frontend/vercel.json) |
| `wealth-intelligence-api` (optional) | `backend` | [`backend/vercel.json`](../backend/vercel.json) |

## 1. Frontend (Next.js) — the primary deployable

1. Import the GitHub repo into Vercel.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Next.js; the
   framework, build, and output settings are also pinned in
   `frontend/vercel.json`.
3. Add one environment variable:

   | Name | Example value | Notes |
   |------|---------------|-------|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://wealth-intelligence-api.vercel.app` | Public — it ships to the browser. Point it at your deployed backend. |

4. Deploy. Security headers (`X-Content-Type-Options`, `X-Frame-Options`,
   `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`) are
   applied via `frontend/vercel.json`.

### CLI alternative

```bash
cd frontend
vercel link                       # select/create the project
vercel env add NEXT_PUBLIC_API_BASE_URL production
vercel --prod
```

## 2. Backend (FastAPI) — optional serverless preview

The backend runs on Vercel's Python runtime via
[`backend/api/index.py`](../backend/api/index.py), which exposes the ASGI `app`.
All routes are rewritten to that function by `backend/vercel.json`. Runtime
dependencies come from [`backend/requirements.txt`](../backend/requirements.txt).

1. Create a second Vercel project with **Root Directory** = `backend`.
2. Set environment variables (all prefixed `WIA_`, see
   [`backend/app/core/config.py`](../backend/app/core/config.py)):

   | Name | Purpose | Notes |
   |------|---------|-------|
   | `WIA_ENV` | `prod` / `staging` / `dev` | Tightens CORS off `*` outside `dev`. |
   | `WIA_SECRET_KEY` | JWT signing key | **Set a long random string. Never commit it.** |
   | `WIA_DEFAULT_DATA_REGION` | `qa` / `eu` / `global` | Data-residency routing. |
   | `WIA_LLM_PROVIDER` | `stub` (default) or `anthropic` | Stub runs fully offline. |
   | `WIA_LLM_API_KEY` | Anthropic key | Only if `WIA_LLM_PROVIDER=anthropic`; add `anthropic>=1.0` to `requirements.txt`. |

3. Deploy, then verify: `GET https://<api-project>.vercel.app/health`.

### ⚠️ Serverless statelessness

The scaffold uses an **in-memory repository**. On serverless, state does **not**
persist across invocations — each cold start re-seeds demo data, and writes made
in one request may not be visible to the next. This is fine for a demo/preview
but is **not** a production posture. For anything beyond a demo:

- Swap the in-memory repository for a managed database (Postgres via
  `WIA_DATABASE_URL`), and
- Prefer a long-lived host (ECS/Fargate, Fly.io, Railway, Render) over
  serverless for the API, so background report generation and rate-limit state
  behave correctly.

## Wiring the two together

1. Deploy the backend first; note its URL.
2. Set the frontend's `NEXT_PUBLIC_API_BASE_URL` to that URL and redeploy the
   frontend.
3. For production, restrict backend CORS to the frontend's origin (currently
   `allow_origins=["*"]` only when `WIA_ENV=dev`; tighten
   [`backend/app/main.py`](../backend/app/main.py) to the deployed frontend
   origin for `staging`/`prod`).

## Compliance notes

- **Data residency:** Vercel's global edge is convenient for previews but does
  not satisfy Qatar in-region residency requirements. Production stays on the
  region-pinned AWS topology in [`infra/README.md`](../infra/README.md).
- **Secrets:** managed only through Vercel env vars / a secrets manager — never
  in `vercel.json`, source, or committed `.env` files.
