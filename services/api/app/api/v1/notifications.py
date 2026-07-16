"""In-app notification routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_scopes
from app.application.notification_service import notification_service
from app.core.database import get_db
from app.domain.auth.scopes import Scope
from app.infrastructure.models.notification import Notification
from app.schemas.notifications import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(require_scopes(Scope.NOTIFICATIONS_READ)),
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    items, total = await notification_service.list_for_user(
        db,
        user_id=current.user_id,
        unread_only=unread_only,
        limit=page_size,
        offset=offset,
    )
    unread_result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current.user_id, Notification.read_at.is_(None))
    )
    unread_count = unread_result.scalar_one()
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
        unread_count=unread_count,
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(require_scopes(Scope.NOTIFICATIONS_WRITE)),
):
    notification = await notification_service.mark_read(
        db, user_id=current.user_id, notification_id=notification_id
    )
    await db.commit()
    return notification


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(require_scopes(Scope.NOTIFICATIONS_WRITE)),
):
    marked = await notification_service.mark_all_read(db, user_id=current.user_id)
    await db.commit()
    return MarkAllReadResponse(marked=marked)
