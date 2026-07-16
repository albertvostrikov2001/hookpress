"""Auth routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    bearer_scheme,
    client_ip,
    get_current_user,
    refresh_token_from_request,
)
from app.application.auth_service import auth_service
from app.core import redis as redis_core
from app.core.config import settings
from app.core.database import get_db
from app.infrastructure.security.jwt import decode_access_token
from app.schemas.auth import (
    AuthResponse,
    DevLoginRequest,
    OAuthStartResponse,
    SessionResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=[r.role for r in user.roles],
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.jwt_refresh_ttl_days * 24 * 3600
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.refresh_cookie_name, path="/api/v1/auth")


@router.post("/dev-login", response_model=AuthResponse)
async def dev_login(
    body: DevLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    access, refresh, user = await auth_service.dev_login(
        db,
        redis_core.redis_client,
        email=body.email,
        ip_address=client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    _set_refresh_cookie(response, refresh)
    return AuthResponse(
        tokens=TokenResponse(
            access_token=access,
            expires_in=settings.jwt_access_ttl_minutes * 60,
        ),
        user=_user_response(user),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str, Depends(refresh_token_from_request)],
):
    access, new_refresh, user = await auth_service.refresh(
        db,
        refresh_token=refresh_token,
        ip_address=client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    _set_refresh_cookie(response, new_refresh)
    return AuthResponse(
        tokens=TokenResponse(
            access_token=access,
            expires_in=settings.jwt_access_ttl_minutes * 60,
        ),
        user=_user_response(user),
    )


@router.post("/logout", status_code=204, response_class=Response)
async def logout(
    response: Response,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    refresh_cookie: Annotated[str | None, Cookie(alias="hookpress_refresh")] = None,
):
    user_id = None
    if credentials and credentials.scheme.lower() == "bearer":
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    await auth_service.logout(db, refresh_token=refresh_cookie or "", user_id=user_id)
    _clear_refresh_cookie(response)
    return Response(status_code=204)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    sessions = await auth_service.list_sessions(db, current.user_id)
    return sessions


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    await auth_service.revoke_session(db, current.user_id, session_id)
    return Response(status_code=204)


@router.post("/sessions/revoke-all", status_code=204)
async def revoke_all_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    await auth_service.revoke_all_sessions(db, current.user_id)
    return Response(status_code=204)


@router.get("/oauth/{provider}/start", response_model=OAuthStartResponse)
async def oauth_start(provider: str):
    redirect_url = await auth_service.oauth_start(redis_core.redis_client, provider_name=provider)
    return OAuthStartResponse(redirect_url=redirect_url, provider=provider)


@router.get("/oauth/{provider}/callback", response_model=AuthResponse)
async def oauth_callback(
    provider: str,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    code: Annotated[str, Query()],
    state: Annotated[str, Query()],
):
    access, refresh, user = await auth_service.oauth_callback(
        db,
        redis_core.redis_client,
        provider_name=provider,
        code=code,
        state=state,
        ip_address=client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    _set_refresh_cookie(response, refresh)
    return AuthResponse(
        tokens=TokenResponse(
            access_token=access,
            expires_in=settings.jwt_access_ttl_minutes * 60,
        ),
        user=_user_response(user),
    )
