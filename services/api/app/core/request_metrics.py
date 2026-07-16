"""Prometheus and request metrics middleware."""

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import HTTP_ERRORS, HTTP_REQUESTS


def _metric_path(path: str) -> str:
    if path.startswith("/api/v1/auth"):
        return "/api/v1/auth"
    if path.startswith("/api/v1/studio"):
        return "/api/v1/studio"
    if path.startswith("/api/v1/billing"):
        return "/api/v1/billing"
    return path.split("?")[0][:64]


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        path = _metric_path(request.url.path)
        status = str(response.status_code)
        HTTP_REQUESTS.labels(request.method, path, status).inc()
        if response.status_code >= 400:
            HTTP_ERRORS.labels(request.method, path, status).inc()
        return response
