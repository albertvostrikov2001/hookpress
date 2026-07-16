"""FastAPI dependencies."""

import uuid
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.idempotency_service import hash_request, idempotency_service
from app.core.database import get_db
from app.core.errors import AppError
from app.domain.auth.roles import Role
from app.domain.auth.scopes import Scope, scopes_from_payload
from app.infrastructure.models.user import User
from app.infrastructure.security.jwt import decode_access_token, roles_from_payload

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        user_id: uuid.UUID,
        email: str,
        roles: set[Role],
        scopes: set[Scope],
    ):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.scopes = scopes

    def has_any_role(self, *roles: Role) -> bool:
        return bool(self.roles.intersection(roles))

    def has_scope(self, *scopes: Scope) -> bool:
        if Scope.ADMIN in self.scopes:
            return True
        return bool(self.scopes.intersection(scopes))


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("unauthorized", "Authentication required", status_code=401)
    payload = decode_access_token(credentials.credentials)
    return CurrentUser(
        user_id=uuid.UUID(payload["sub"]),
        email=payload["email"],
        roles=roles_from_payload(payload),
        scopes=scopes_from_payload(payload),
    )


async def optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return CurrentUser(
            user_id=uuid.UUID(payload["sub"]),
            email=payload["email"],
            roles=roles_from_payload(payload),
            scopes=scopes_from_payload(payload),
        )
    except AppError:
        return None


def require_roles(*required: Role):
    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not user.has_any_role(*required):
            raise AppError("forbidden", "Insufficient permissions", status_code=403)
        return user

    return checker


def require_scopes(*required: Scope):
    async def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not user.has_scope(*required):
            raise AppError("forbidden", "Insufficient scope", status_code=403)
        return user

    return checker


@dataclass
class IdempotencyContext:
    key: str
    method: str
    path: str
    request_hash: str
    replay_body: dict[str, Any] | None = None
    replay_status: int | None = None


def require_idempotency():
    async def dependency(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_db)],
        current: Annotated[CurrentUser, Depends(get_current_user)],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> IdempotencyContext:
        if not idempotency_key:
            raise AppError("idempotency_required", "Idempotency-Key header required", status_code=400)
        body = await request.body()
        req_hash = hash_request(request.method, request.url.path, body)
        record = await idempotency_service.lookup(
            db, user_id=current.user_id, key=idempotency_key
        )
        if record is not None:
            idempotency_service.assert_same_request(record, req_hash)
            return IdempotencyContext(
                key=idempotency_key,
                method=request.method,
                path=request.url.path,
                request_hash=req_hash,
                replay_body=record.response_body,
                replay_status=record.response_status,
            )
        return IdempotencyContext(
            key=idempotency_key,
            method=request.method,
            path=request.url.path,
            request_hash=req_hash,
        )

    return dependency


async def get_user_entity(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == current.user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise AppError("user_not_found", "User not found", status_code=404)
    return user


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def refresh_token_from_request(
    authorization: Annotated[str | None, Header()] = None,
    refresh_cookie: Annotated[str | None, Cookie(alias="hookpress_refresh")] = None,
) -> str:
    if refresh_cookie:
        return refresh_cookie
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    raise AppError("invalid_refresh_token", "Refresh token required", status_code=401)
