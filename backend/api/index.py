"""Vercel serverless entrypoint for the FastAPI backend.

Vercel's Python runtime (`@vercel/python`) detects the module-level ``app``
ASGI application and serves it. All routes are rewritten to this function via
``backend/vercel.json``.

NOTE: the scaffold uses an in-memory repository, so state does NOT persist
across serverless invocations (each cold start re-seeds demo data). This entry
is suitable for demos and previews; a production deployment swaps the in-memory
repository for a managed database (see infra/README.md) and typically runs the
backend on a long-lived host (ECS/Fargate, Fly, Railway) rather than serverless.
"""

from __future__ import annotations

import os
import sys

# Make the backend package importable when Vercel invokes this file directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

__all__ = ["app"]
