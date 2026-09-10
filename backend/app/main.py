"""FastAPI application factory.

Wires middleware (request id + structured logging), the v1 router, health, and
the demo seed. The observed/derived/narrative discipline and compliance
guardrails live in the services layer; this file just assembles the app.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, get_logger, new_request_id
from app.seed import seed
from app.services.ai.guardrails import ComplianceViolation

log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    token = seed()
    log.info("seeded demo data", extra={"extra_fields": {"demo_access_token": token}})
    print("\n" + "=" * 72)
    print("Wealth Intelligence AI — demo access token (Authorize in /docs):")
    print(f"  {token}")
    print("=" * 72 + "\n")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="AI-powered wealth banking & intelligence — observed/derived/narrative, "
        "never mutating source data. Information & advisory only.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.env == "dev" else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(ComplianceViolation)
    async def compliance_handler(request: Request, exc: ComplianceViolation):
        # A blocked output must never leak — return a problem+json error.
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "Compliance violation",
                "status": 422,
                "detail": f"output blocked by rule {exc}",
            },
        )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "env": settings.env, "data_region": settings.default_data_region}

    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
