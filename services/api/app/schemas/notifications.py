"""Notification API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginatedResponse


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: str | None
    data: dict | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    unread_count: int = Field(ge=0)


class MarkAllReadResponse(BaseModel):
    marked: int
