"""CSRF protection for cookie-authenticated POST routes."""

import secrets
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

CSRF_COOKIE = "hookpress_csrf"
CSRF_HEADER = "X-CSRF-Token"
PROTECTED_PREFIXES = ("/api/v1/auth/refresh", "/api/v1/auth/logout")


def _uses_bearer_auth(request: Request) -> bool:
    auth = request.headers.get("Authorization", "")
    return auth.lower().startswith("bearer ")


def _requires_csrf(request: Request) -> bool:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    path = request.url.path
    if not any(path == prefix or path.startswith(f"{prefix}/") for prefix in PROTECTED_PREFIXES):
        return False
    if _uses_bearer_auth(request):
        return False
    return request.cookies.get(settings.refresh_cookie_name) is not None


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if _requires_csrf(request):
            cookie_token = request.cookies.get(CSRF_COOKIE)
            header_token = request.headers.get(CSRF_HEADER)
            if not cookie_token or not header_token or cookie_token != header_token:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {
                            "code": "csrf_failed",
                            "message": "CSRF token missing or invalid",
                        }
                    },
                )

        response = await call_next(request)

        if CSRF_COOKIE not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=CSRF_COOKIE,
                value=token,
                httponly=False,
                secure=settings.cookie_secure,
                samesite="lax",
                path="/",
            )

        return response
