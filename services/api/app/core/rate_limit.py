"""Redis-backed rate limiting middleware."""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {"/health", "/ready", "/metrics", "/api/v1/setup/seed", "/api/v1/setup/status"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter using Redis INCR."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in EXEMPT_PATHS or path.startswith("/api/v1/docs") or path.startswith("/api/v1/openapi"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time()) // settings.rate_limit_window_seconds
        key = f"rl:{client_ip}:{window}"

        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, settings.rate_limit_window_seconds)
            if count > settings.rate_limit_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": "Too many requests. Please retry later.",
                            "details": {"limit": settings.rate_limit_requests},
                        }
                    },
                    headers={"Retry-After": str(settings.rate_limit_window_seconds)},
                )
        except Exception:
            logger.warning("rate limit check failed; allowing request", exc_info=True)

        return await call_next(request)
