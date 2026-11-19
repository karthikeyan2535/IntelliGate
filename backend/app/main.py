"""
FastAPI application entry point for IntelliGate.
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1 import (
    analytics,
    auth,
    budget_policies,
    cache,
    coding,
    evaluation,
    gateway,
    keys,
    logs,
    models,
    orgs,
    projects,
    providers,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, set_request_id
from app.core.metrics import APP_INFO, HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL
from app.database.base import engine

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_logging(settings.LOG_LEVEL, json_logs=settings.ENVIRONMENT != "development")
    APP_INFO.info(
        {
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )
    from app.providers.registry import provider_registry
    provider_registry.ensure_initialized()

    # Ensure database tables exist
    try:
        from app.database.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully")
    except Exception as db_init_err:
        logger.warning("Database table initialization notice", error=str(db_init_err))

    logger.info("IntelliGate starting", version=settings.APP_VERSION)

    yield

    # Shutdown
    logger.info("IntelliGate shutting down")
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade multi-provider LLM gateway",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS middleware ───────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # ── Request ID middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        # Metrics
        path = request.url.path
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status_code=response.status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(duration)

        return response

    # ── Exception handlers ────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "An internal server error occurred.",
                    "type": "internal_server_error",
                    "code": "internal_error",
                }
            },
        )

    from fastapi import HTTPException

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "api_error",
                    "code": f"http_{exc.status_code}",
                }
            },
        )

    # ── Health endpoint ───────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # ── Metrics endpoint (Prometheus) ─────────────────────────────────────
    @app.get("/metrics", tags=["System"], include_in_schema=False)
    async def metrics():
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    # ── API routers ───────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(orgs.router, prefix=API_PREFIX)
    app.include_router(projects.router, prefix=API_PREFIX)
    app.include_router(keys.router, prefix=API_PREFIX)
    app.include_router(providers.router, prefix=API_PREFIX)
    app.include_router(models.router, prefix=API_PREFIX)
    app.include_router(budget_policies.router, prefix=API_PREFIX)
    app.include_router(analytics.router, prefix=API_PREFIX)
    app.include_router(coding.router, prefix=API_PREFIX)
    app.include_router(evaluation.router, prefix=API_PREFIX)
    app.include_router(logs.router, prefix=API_PREFIX)
    app.include_router(cache.router, prefix=API_PREFIX)

    # ── OpenAI-compatible Gateway endpoints (/v1/chat/completions, /v1/models)
    app.include_router(gateway.router)

    return app


app = create_app()
