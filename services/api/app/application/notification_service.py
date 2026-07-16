"""Notification use cases."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.infrastructure.models.notification import Notification


class NotificationService:
    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        type: str,
        title: str,
        body: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data,
        )
        db.add(notification)
        await db.flush()
        return notification

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base = base.where(Notification.read_at.is_(None))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        result = await db.execute(
            base.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise AppError("notification_not_found", "Notification not found", status_code=404)
        return notification

    async def mark_read(
        self, db: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Notification:
        notification = await self.get_for_user(db, user_id=user_id, notification_id=notification_id)
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)
            await db.flush()
        return notification

    async def mark_all_read(self, db: AsyncSession, *, user_id: uuid.UUID) -> int:
        now = datetime.now(UTC)
        result = await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=now)
        )
        await db.flush()
        return result.rowcount or 0


notification_service = NotificationService()
