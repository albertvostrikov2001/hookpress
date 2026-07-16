"""HTTP idempotency key storage."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.infrastructure.models.idempotency_key import IdempotencyKey

DEFAULT_TTL_HOURS = 24


def hash_request(method: str, path: str, body: bytes = b"") -> str:
    digest = hashlib.sha256()
    digest.update(method.upper().encode())
    digest.update(b":")
    digest.update(path.encode())
    digest.update(b":")
    digest.update(body)
    return digest.hexdigest()


def hash_response(body: dict[str, Any]) -> str:
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


class IdempotencyService:
    async def lookup(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        key: str,
    ) -> IdempotencyKey | None:
        result = await db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.user_id == user_id,
                IdempotencyKey.key == key,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        if record.expires_at and record.expires_at < datetime.now(UTC):
            return None
        return record

    async def store(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        key: str,
        method: str,
        path: str,
        request_hash: str,
        response_status: int,
        response_body: dict[str, Any],
        ttl_hours: int = DEFAULT_TTL_HOURS,
    ) -> IdempotencyKey:
        body_hash = hash_response(response_body)
        record = IdempotencyKey(
            user_id=user_id,
            key=key,
            method=method.upper(),
            path=path,
            request_hash=request_hash,
            response_status=response_status,
            response_body_hash=body_hash,
            response_body=response_body,
            expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
        )
        db.add(record)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            existing = await self.lookup(db, user_id=user_id, key=key)
            if existing is None:
                raise
            if existing.request_hash != request_hash:
                raise AppError(
                    "idempotency_conflict",
                    "Idempotency key reused with different request",
                    status_code=409,
                )
            return existing
        return record

    def assert_same_request(self, record: IdempotencyKey, request_hash: str) -> None:
        if record.request_hash != request_hash:
            raise AppError(
                "idempotency_conflict",
                "Idempotency key reused with different request",
                status_code=409,
            )


idempotency_service = IdempotencyService()
