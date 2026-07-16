"""Chat REST and WebSocket routes."""

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.chat_service import chat_service
from app.core.database import SessionLocal, get_db
from app.core.errors import AppError
from app.core.metrics import WS_CONNECTIONS
from app.core.redis import redis_client
from app.infrastructure.security.jwt import decode_access_token
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessagesPage,
    ChatReadStatusUpdate,
    ChatRoomCreate,
    ChatRoomResponse,
)

router = APIRouter(tags=["chat"])


@router.post("/chat/rooms", response_model=ChatRoomResponse)
async def create_room(
    body: ChatRoomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    member_ids = list(set(body.member_ids) | {current.user_id})
    room = await chat_service.create_room(
        db, name=body.name, member_ids=member_ids, room_type=body.room_type
    )
    await db.commit()
    return room


@router.get("/chat/rooms", response_model=list[ChatRoomResponse])
async def list_rooms(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
    limit: int = Query(default=50, le=100),
):
    rooms = await chat_service.list_user_rooms(db, user_id=current.user_id, limit=limit)
    return [ChatRoomResponse.model_validate(r) for r in rooms]


@router.get("/chat/rooms/{room_id}/messages", response_model=ChatMessagesPage)
async def list_messages(
    room_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    cursor: str | None = Query(default=None),
):
    await chat_service.assert_member(db, room_id, current.user_id)
    messages, next_cursor, has_more = await chat_service.list_messages(
        db, room_id, limit=limit, cursor=cursor
    )
    return ChatMessagesPage(
        items=[ChatMessageResponse.model_validate(m) for m in messages],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post("/chat/rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    room_id: uuid.UUID,
    body: ChatMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    message = await chat_service.send_message(
        db,
        redis_client,
        room_id=room_id,
        sender_id=current.user_id,
        body=body.body,
        client_message_id=body.client_message_id,
        media_asset_id=body.media_asset_id,
    )
    return message


@router.post("/chat/rooms/{room_id}/read")
async def update_read_status(
    room_id: uuid.UUID,
    body: ChatReadStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    await chat_service.assert_member(db, room_id, current.user_id)
    await chat_service.set_read_status(
        redis_client,
        room_id=room_id,
        user_id=current.user_id,
        message_id=body.message_id,
    )
    event = {
        "type": "read_status",
        "room_id": str(room_id),
        "user_id": str(current.user_id),
        "message_id": str(body.message_id),
    }
    await chat_service.publish_event(redis_client, room_id, event)
    return {"status": "ok"}


async def _authenticate_ws(token: str | None) -> uuid.UUID:
    if not token:
        raise AppError("unauthorized", "Authentication required", status_code=401)
    payload = decode_access_token(token)
    return uuid.UUID(payload["sub"])


@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: uuid.UUID,
    token: str | None = Query(default=None),
):
    try:
        user_id = await _authenticate_ws(token)
    except AppError:
        await websocket.close(code=4401)
        return

    async with SessionLocal() as db:
        try:
            await chat_service.assert_member(db, room_id, user_id)
        except AppError:
            await websocket.close(code=4403)
            return

    await websocket.accept()
    WS_CONNECTIONS.inc()
    await chat_service.set_presence(redis_client, room_id=room_id, user_id=user_id)
    await chat_service.publish_event(
        redis_client,
        room_id,
        {"type": "presence", "room_id": str(room_id), "user_id": str(user_id), "status": "online"},
    )

    async def relay_redis():
        async for event in chat_service.subscribe_room(redis_client, room_id):
            await websocket.send_json(event)

    relay_task = asyncio.create_task(relay_redis())
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            event_type = data.get("type", "message")

            if event_type == "typing":
                if data.get("active"):
                    await chat_service.set_typing(redis_client, room_id=room_id, user_id=user_id)
                else:
                    await chat_service.clear_typing(redis_client, room_id=room_id, user_id=user_id)
                await chat_service.publish_event(
                    redis_client,
                    room_id,
                    {
                        "type": "typing",
                        "room_id": str(room_id),
                        "user_id": str(user_id),
                        "active": bool(data.get("active")),
                    },
                )
                continue

            if event_type == "read_status":
                message_id = data.get("message_id")
                if message_id:
                    await chat_service.set_read_status(
                        redis_client,
                        room_id=room_id,
                        user_id=user_id,
                        message_id=uuid.UUID(message_id),
                    )
                    await chat_service.publish_event(
                        redis_client,
                        room_id,
                        {
                            "type": "read_status",
                            "room_id": str(room_id),
                            "user_id": str(user_id),
                            "message_id": message_id,
                        },
                    )
                continue

            if event_type == "presence":
                await chat_service.set_presence(redis_client, room_id=room_id, user_id=user_id)
                await chat_service.publish_event(
                    redis_client,
                    room_id,
                    {
                        "type": "presence",
                        "room_id": str(room_id),
                        "user_id": str(user_id),
                        "status": "online",
                    },
                )
                continue

            body = data.get("body", "")
            client_message_id = data.get("client_message_id") or str(uuid.uuid4())
            media_asset_id = data.get("media_asset_id")
            parsed_media_id = uuid.UUID(media_asset_id) if media_asset_id else None
            async with SessionLocal() as db:
                message = await chat_service.send_message(
                    db,
                    redis_client,
                    room_id=room_id,
                    sender_id=user_id,
                    body=body,
                    client_message_id=client_message_id,
                    media_asset_id=parsed_media_id,
                )
                await websocket.send_json(
                    {
                        **chat_service._message_payload(message),
                        "echo": True,
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        WS_CONNECTIONS.dec()
        await chat_service.clear_presence(redis_client, room_id=room_id, user_id=user_id)
        await chat_service.publish_event(
            redis_client,
            room_id,
            {"type": "presence", "room_id": str(room_id), "user_id": str(user_id), "status": "offline"},
        )
        relay_task.cancel()
        try:
            await relay_task
        except asyncio.CancelledError:
            pass
