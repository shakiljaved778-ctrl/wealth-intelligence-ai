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

## Troubleshooting

### The frontend builds but shows no data / network errors in the browser

This is almost always the env variable, because `NEXT_PUBLIC_API_BASE_URL` is
**inlined at build time**, not read at runtime:

1. It must be set in **Project → Settings → Environment Variables** for the
   **Production** (and **Preview**) environment.
2. After adding or changing it you must **redeploy** (a fresh build) — an
   existing deployment keeps the value baked into its bundle. Changing the env
   var alone does nothing until a rebuild.
3. If it is unset, `lib/api.ts` and `next.config.js` fall back to
   `http://localhost:8000`, so the browser tries to reach *the visitor's own
   machine* and every API call fails. That is the classic "deployed but nothing
   loads" symptom.

Verify from the deployed page's devtools → Network: the requests should target
your backend URL, not `localhost:8000`. If they hit localhost, the build did not
receive the env var — re-check the variable's **environment scope** and redeploy.

To make this self-evident, the login screen shows the resolved **API endpoint**
it was built with, and — when the site is served from a non-local host but the
API URL still points at `localhost` — a red warning saying the env var wasn't
set at build time. If you see that warning, set `NEXT_PUBLIC_API_BASE_URL` and
redeploy. Login errors also distinguish an unreachable API from bad credentials.

### The frontend deploy itself fails

- Do **not** set `outputDirectory` for a Next.js app — the `nextjs` framework
  preset manages output via Vercel's Build Output API. Overriding it (e.g. to
  `.next`) makes Vercel treat that as a static folder and breaks the
  server-rendered `/assets/[symbol]` route. This repo's `frontend/vercel.json`
  intentionally sets only `framework` + `headers`.
- Confirm **Root Directory = `frontend`** in project settings.

### The backend function fails to build or 404s

- Do **not** pin the Python runtime to a specific patch (e.g.
  `@vercel/python@4.3.1`) — an unpublished version yields
  *"The specified Runtime … can not be found."* Let the `.py` files under
  `api/` auto-select the official runtime; `backend/vercel.json` only sets
  `maxDuration` + the catch-all rewrite.
- Confirm **Root Directory = `backend`**, that `backend/requirements.txt`
  exists, and that `GET /health` returns `{"status":"ok"}`.
- Remember the in-memory store is **not** shared across invocations (see the
  statelessness note above) — data written in one request may vanish on the
  next. That is expected on serverless, not a bug.

## Compliance notes

- **Data residency:** Vercel's global edge is convenient for previews but does
  not satisfy Qatar in-region residency requirements. Production stays on the
  region-pinned AWS topology in [`infra/README.md`](../infra/README.md).
- **Secrets:** managed only through Vercel env vars / a secrets manager — never
  in `vercel.json`, source, or committed `.env` files.
