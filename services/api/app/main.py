"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.csrf import CsrfMiddleware
from app.core.database import engine
from app.core.errors import AppError, app_error_handler, http_error_handler, validation_error_handler
from app.core.logging import setup_logging
from app.core.metrics import metrics_response
from app.core.middleware import CorrelationIdMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.request_metrics import MetricsMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.telemetry import setup_otel, setup_sentry


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    setup_sentry()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )

    setup_otel(app)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "api"}

    @app.get("/ready")
    async def ready():
        from app.core.redis import ping_redis
        from app.infrastructure.storage.s3_health import ping_s3

        checks: dict[str, bool] = {"api": True}
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = True
        except Exception:
            checks["database"] = False
        checks["redis"] = await ping_redis()
        checks["s3"] = await ping_s3()
        status = "ready" if all(checks.values()) else "degraded"
        return {"status": status, "checks": checks}

    @app.get("/metrics")
    async def metrics():
        body, content_type = metrics_response()
        return Response(content=body, media_type=content_type)

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
