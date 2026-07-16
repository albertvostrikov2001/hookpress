"""Authentication use cases."""

import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.audit import write_audit
from app.core.config import settings
from app.core.errors import AppError
from app.domain.auth.roles import DEFAULT_SIGNUP_ROLES, Role
from app.domain.auth.scopes import scopes_for_roles
from app.infrastructure.models.login_event import LoginEvent
from app.infrastructure.models.session import Session
from app.infrastructure.models.user import User
from app.infrastructure.models.user_role import UserRole
from app.infrastructure.providers.oauth import OAuthUserInfo, get_oauth_provider, oauth_redirect_uri
from app.infrastructure.security.jwt import create_access_token
from app.infrastructure.security.tokens import generate_refresh_token, hash_refresh_token


class AuthService:
    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def _lockout_keys(self, email: str) -> tuple[str, str]:
        normalized = self._normalize_email(email)
        return f"login:failures:{normalized}", f"login:locked:{normalized}"

    async def _is_locked_out(self, redis: Redis, email: str) -> bool:
        _, locked_key = self._lockout_keys(email)
        return bool(await redis.get(locked_key))

    async def _record_failed_login(self, redis: Redis, email: str) -> None:
        failures_key, locked_key = self._lockout_keys(email)
        count = await redis.incr(failures_key)
        if count == 1:
            await redis.expire(failures_key, settings.login_lockout_ttl_seconds)
        if count >= settings.login_lockout_max_attempts:
            await redis.setex(locked_key, settings.login_lockout_ttl_seconds, "1")

    async def _clear_login_lockout(self, redis: Redis, email: str) -> None:
        failures_key, locked_key = self._lockout_keys(email)
        await redis.delete(failures_key, locked_key)

    async def _record_login_event(
        self,
        db: AsyncSession,
        *,
        email: str,
        method: str,
        success: bool,
        user_id: uuid.UUID | None = None,
        failure_reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        db.add(
            LoginEvent(
                user_id=user_id,
                email=email,
                method=method,
                success=success,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        await db.flush()

    async def dev_login(
        self,
        db: AsyncSession,
        redis: Redis,
        *,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str, User]:
        if not settings.dev_login_enabled:
            raise AppError("dev_login_disabled", "Dev login is disabled", status_code=403)

        if await self._is_locked_out(redis, email):
            await self._record_login_event(
                db,
                email=email,
                method="dev_login",
                success=False,
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await db.commit()
            raise AppError(
                "account_locked",
                "Too many failed login attempts. Try again later.",
                status_code=429,
            )

        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user is None:
            await self._record_failed_login(redis, email)
            await self._record_login_event(
                db,
                email=email,
                method="dev_login",
                success=False,
                failure_reason="user_not_found",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await db.commit()
            raise AppError("user_not_found", "User not found. Run seed script first.", status_code=404)

        await self._clear_login_lockout(redis, email)
        access, refresh = await self._create_session(
            db, user=user, ip_address=ip_address, user_agent=user_agent
        )
        await self._record_login_event(
            db,
            email=email,
            method="dev_login",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await write_audit(
            db,
            action="auth.dev_login",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=user.id,
            ip_address=ip_address,
            metadata={"email": email},
        )
        await db.commit()
        return access, refresh, user

    async def oauth_start(self, redis: Redis, *, provider_name: str) -> str:
        provider = get_oauth_provider(provider_name)
        state = secrets.token_urlsafe(32)
        redirect_uri = oauth_redirect_uri(provider_name)
        await redis.setex(
            f"oauth:state:{state}",
            settings.oauth_state_ttl_seconds,
            json.dumps({"provider": provider_name}),
        )
        return await provider.get_authorization_url(state=state, redirect_uri=redirect_uri)

    async def oauth_callback(
        self,
        db: AsyncSession,
        redis: Redis,
        *,
        provider_name: str,
        code: str,
        state: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str, User]:
        state_key = f"oauth:state:{state}"
        stored = await redis.get(state_key)
        if not stored:
            raise AppError("invalid_oauth_state", "Invalid or expired OAuth state", status_code=400)
        payload = json.loads(stored)
        if payload.get("provider") != provider_name:
            raise AppError("invalid_oauth_state", "OAuth state provider mismatch", status_code=400)
        await redis.delete(state_key)

        provider = get_oauth_provider(provider_name)
        redirect_uri = oauth_redirect_uri(provider_name)
        try:
            oauth_user = await provider.exchange_code(code=code, redirect_uri=redirect_uri)
        except AppError as exc:
            await self._record_login_event(
                db,
                email="",
                method=f"oauth_{provider_name}",
                success=False,
                failure_reason=exc.code,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await db.commit()
            raise

        user = await self._find_or_create_oauth_user(db, provider_name, oauth_user)
        access, refresh = await self._create_session(
            db, user=user, ip_address=ip_address, user_agent=user_agent
        )
        await self._record_login_event(
            db,
            email=user.email,
            method=f"oauth_{provider_name}",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await write_audit(
            db,
            action="auth.oauth_login",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=user.id,
            ip_address=ip_address,
            metadata={"provider": provider_name, "email": user.email},
        )
        await db.commit()
        return access, refresh, user

    async def _find_or_create_oauth_user(
        self,
        db: AsyncSession,
        provider_name: str,
        oauth_user: OAuthUserInfo,
    ) -> User:
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.oauth_provider == provider_name, User.oauth_subject == oauth_user.subject)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            return user

        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == oauth_user.email)
        )
        user = result.scalar_one_or_none()
        if user is not None:
            user.oauth_provider = provider_name
            user.oauth_subject = oauth_user.subject
            await db.flush()
            return user

        user = User(
            email=oauth_user.email,
            display_name=oauth_user.display_name,
            oauth_provider=provider_name,
            oauth_subject=oauth_user.subject,
        )
        db.add(user)
        await db.flush()
        for role in DEFAULT_SIGNUP_ROLES:
            db.add(UserRole(user_id=user.id, role=role))
        await db.flush()
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        return result.scalar_one()

    async def refresh(
        self,
        db: AsyncSession,
        *,
        refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str, User]:
        token_hash = hash_refresh_token(refresh_token)
        result = await db.execute(
            select(Session)
            .where(Session.refresh_token_hash == token_hash)
            .options(selectinload(Session.user).selectinload(User.roles))
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise AppError("invalid_refresh_token", "Invalid refresh token", status_code=401)

        now = datetime.now(UTC)
        if session.revoked_at is not None:
            await self._revoke_family(db, session.family_id, now)
            await db.commit()
            raise AppError("refresh_token_reuse", "Refresh token reuse detected", status_code=401)

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            raise AppError("invalid_refresh_token", "Refresh token expired", status_code=401)

        session.revoked_at = now
        user = session.user
        access, new_refresh = await self._create_session(
            db,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            family_id=session.family_id,
        )
        await write_audit(
            db,
            action="auth.refresh",
            resource_type="session",
            resource_id=str(session.id),
            actor_user_id=user.id,
            ip_address=ip_address,
        )
        await db.commit()
        return access, new_refresh, user

    async def logout(
        self,
        db: AsyncSession,
        *,
        refresh_token: str,
        user_id: uuid.UUID | None,
    ) -> None:
        token_hash = hash_refresh_token(refresh_token)
        now = datetime.now(UTC)
        result = await db.execute(select(Session).where(Session.refresh_token_hash == token_hash))
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = now
            await write_audit(
                db,
                action="auth.logout",
                resource_type="session",
                resource_id=str(session.id),
                actor_user_id=session.user_id,
            )
        elif user_id:
            await db.execute(
                update(Session)
                .where(Session.user_id == user_id, Session.revoked_at.is_(None))
                .values(revoked_at=now)
            )
            await write_audit(
                db,
                action="auth.logout_all",
                resource_type="user",
                resource_id=str(user_id),
                actor_user_id=user_id,
            )
        await db.commit()

    async def list_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> list[Session]:
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .order_by(Session.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_session(self, db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        result = await db.execute(
            select(Session).where(Session.id == session_id, Session.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise AppError("session_not_found", "Session not found", status_code=404)
        session.revoked_at = datetime.now(UTC)
        await write_audit(
            db,
            action="auth.revoke_session",
            resource_type="session",
            resource_id=str(session_id),
            actor_user_id=user_id,
        )
        await db.commit()

    async def revoke_all_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        now = datetime.now(UTC)
        result = await db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.revoked_at.is_(None))
            .values(revoked_at=now)
            .returning(Session.id)
        )
        revoked_ids = list(result.scalars().all())
        await write_audit(
            db,
            action="auth.revoke_all_sessions",
            resource_type="user",
            resource_id=str(user_id),
            actor_user_id=user_id,
            metadata={"count": len(revoked_ids)},
        )
        await db.commit()
        return len(revoked_ids)

    async def list_login_events(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[LoginEvent]:
        result = await db.execute(
            select(LoginEvent)
            .where(LoginEvent.user_id == user_id)
            .order_by(LoginEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_user_roles(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        roles: list[str],
        actor_user_id: uuid.UUID,
    ) -> User:
        valid_roles = {role.value for role in Role}
        invalid = [role for role in roles if role not in valid_roles]
        if invalid:
            raise AppError(
                "invalid_roles",
                "One or more roles are invalid",
                status_code=400,
                details={"invalid": invalid},
            )

        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise AppError("user_not_found", "User not found", status_code=404)

        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        for role in roles:
            db.add(UserRole(user_id=user_id, role=role))
        await db.flush()

        await write_audit(
            db,
            action="admin.set_user_roles",
            resource_type="user",
            resource_id=str(user_id),
            actor_user_id=actor_user_id,
            metadata={"roles": roles},
        )
        await db.commit()

        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return result.scalar_one()

    async def _create_session(
        self,
        db: AsyncSession,
        *,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
        family_id: uuid.UUID | None = None,
    ) -> tuple[str, str]:
        refresh_token = generate_refresh_token()
        roles = [r.role for r in user.roles]
        scopes = scopes_for_roles(roles)
        access = create_access_token(user_id=user.id, email=user.email, roles=roles, scopes=scopes)
        now = datetime.now(UTC)
        session = Session(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            refresh_token_hash=hash_refresh_token(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=now + timedelta(days=settings.jwt_refresh_ttl_days),
        )
        db.add(session)
        await db.flush()
        return access, refresh_token

    async def _revoke_family(self, db: AsyncSession, family_id: uuid.UUID, now: datetime) -> None:
        await db.execute(
            update(Session)
            .where(Session.family_id == family_id, Session.revoked_at.is_(None))
            .values(revoked_at=now)
        )


auth_service = AuthService()
