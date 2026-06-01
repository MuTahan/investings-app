"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.providers.container import ProviderContainer

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    logger.info("startup", extra={"environment": settings.environment})
    # Long-lived provider container (shared httpx clients + cache).
    app.state.providers = ProviderContainer(settings)
    app.state.scheduler = _maybe_start_scheduler(app, settings)
    try:
        yield
    finally:
        if app.state.scheduler is not None:
            app.state.scheduler.shutdown()
        await app.state.providers.aclose()
        logger.info("shutdown")


def _maybe_start_scheduler(app: FastAPI, settings: Settings):
    if not settings.scheduler_enabled or settings.scheduler_interval_minutes <= 0:
        return None
    from app.db.session import get_sessionmaker
    from app.scheduler.jobs.hourly_recommendations import run_job
    from app.scheduler.scheduler import APSchedulerJobScheduler

    sessionmaker = get_sessionmaker(settings)
    providers = app.state.providers

    async def _job() -> None:
        await run_job(sessionmaker, providers, settings)

    scheduler = APSchedulerJobScheduler()
    scheduler.add_interval_job(_job, settings.scheduler_interval_minutes, "hourly_recommendations")
    scheduler.start()
    return scheduler


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_timing(request: Request, call_next):
        request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
