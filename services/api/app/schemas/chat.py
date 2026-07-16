"""Chat schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.pagination import CursorPage


class ChatRoomCreate(BaseModel):
    name: str = Field(max_length=200)
    member_ids: list[uuid.UUID]
    room_type: str = "GROUP"


class ChatRoomResponse(BaseModel):
    id: uuid.UUID
    name: str
    room_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    body: str
    client_message_id: str = Field(max_length=128)
    media_asset_id: uuid.UUID | None = None


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    client_message_id: str
    body: str
    media_asset_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessagesPage(CursorPage[ChatMessageResponse]):
    pass


class ChatReadStatusUpdate(BaseModel):
    message_id: uuid.UUID
