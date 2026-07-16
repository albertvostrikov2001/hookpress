"""Chat with Redis pub/sub, presence, typing, read status, and attachments."""

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.infrastructure.models.chat_message import ChatMessage
from app.infrastructure.models.chat_room import ChatRoom
from app.infrastructure.models.chat_room_member import ChatRoomMember
from app.infrastructure.models.media_asset import MediaAsset

PRESENCE_TTL_SECONDS = 60
TYPING_TTL_SECONDS = 5


def room_channel(room_id: uuid.UUID) -> str:
    return f"chat:room:{room_id}"


def presence_key(room_id: uuid.UUID) -> str:
    return f"chat:presence:{room_id}"


def typing_key(room_id: uuid.UUID, user_id: uuid.UUID) -> str:
    return f"chat:typing:{room_id}:{user_id}"


def read_key(room_id: uuid.UUID, user_id: uuid.UUID) -> str:
    return f"chat:read:{room_id}:{user_id}"


class ChatService:
    async def create_room(
        self,
        db: AsyncSession,
        *,
        name: str,
        member_ids: list[uuid.UUID],
        room_type: str = "GROUP",
    ) -> ChatRoom:
        room = ChatRoom(name=name, room_type=room_type)
        db.add(room)
        await db.flush()
        for user_id in set(member_ids):
            db.add(ChatRoomMember(room_id=room.id, user_id=user_id))
        await db.flush()
        return room

    async def list_user_rooms(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatRoom]:
        result = await db.execute(
            select(ChatRoom)
            .join(ChatRoomMember, ChatRoomMember.room_id == ChatRoom.id)
            .where(ChatRoomMember.user_id == user_id)
            .order_by(ChatRoom.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get_room(self, db: AsyncSession, room_id: uuid.UUID) -> ChatRoom:
        result = await db.execute(select(ChatRoom).where(ChatRoom.id == room_id))
        room = result.scalar_one_or_none()
        if room is None:
            raise AppError("room_not_found", "Chat room not found", status_code=404)
        return room

    async def assert_member(self, db: AsyncSession, room_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await db.execute(
            select(ChatRoomMember).where(
                ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user_id
            )
        )
        if result.scalar_one_or_none() is None:
            raise AppError("forbidden", "Not a member of this room", status_code=403)

    async def _validate_media(
        self, db: AsyncSession, *, media_asset_id: uuid.UUID, sender_id: uuid.UUID
    ) -> None:
        result = await db.execute(
            select(MediaAsset).where(MediaAsset.id == media_asset_id, MediaAsset.user_id == sender_id)
        )
        if result.scalar_one_or_none() is None:
            raise AppError("media_not_found", "Media asset not found or not owned by sender", status_code=404)

    async def send_message(
        self,
        db: AsyncSession,
        redis: Redis,
        *,
        room_id: uuid.UUID,
        sender_id: uuid.UUID,
        body: str,
        client_message_id: str,
        media_asset_id: uuid.UUID | None = None,
    ) -> ChatMessage:
        await self.assert_member(db, room_id, sender_id)
        if media_asset_id:
            await self._validate_media(db, media_asset_id=media_asset_id, sender_id=sender_id)
        existing = await db.execute(
            select(ChatMessage).where(
                ChatMessage.room_id == room_id,
                ChatMessage.client_message_id == client_message_id,
            )
        )
        message = existing.scalar_one_or_none()
        if message:
            return message

        message = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            client_message_id=client_message_id,
            body=body,
            media_asset_id=media_asset_id,
        )
        db.add(message)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(
                select(ChatMessage).where(
                    ChatMessage.room_id == room_id,
                    ChatMessage.client_message_id == client_message_id,
                )
            )
            message = result.scalar_one()
            return message

        payload = self._message_payload(message)
        await self.publish_event(redis, room_id, payload)
        await db.commit()
        return message

    def _message_payload(self, message: ChatMessage) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "message",
            "id": str(message.id),
            "room_id": str(message.room_id),
            "sender_id": str(message.sender_id),
            "client_message_id": message.client_message_id,
            "body": message.body,
            "created_at": message.created_at.isoformat(),
        }
        if message.media_asset_id:
            payload["media_asset_id"] = str(message.media_asset_id)
        return payload

    async def publish_event(self, redis: Redis, room_id: uuid.UUID, event: dict[str, Any]) -> None:
        await redis.publish(room_channel(room_id), json.dumps(event))

    async def list_messages(
        self,
        db: AsyncSession,
        room_id: uuid.UUID,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[ChatMessage], str | None, bool]:
        stmt = select(ChatMessage).where(ChatMessage.room_id == room_id)
        if cursor:
            cursor_dt, cursor_id = self._decode_cursor(cursor)
            stmt = stmt.where(
                or_(
                    ChatMessage.created_at < cursor_dt,
                    and_(ChatMessage.created_at == cursor_dt, ChatMessage.id < cursor_id),
                )
            )
        stmt = stmt.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit + 1)
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        messages = list(reversed(rows))
        next_cursor = None
        if has_more and messages:
            oldest = messages[0]
            next_cursor = self._encode_cursor(oldest.created_at, oldest.id)
        return messages, next_cursor, has_more

    def _encode_cursor(self, created_at: datetime, message_id: uuid.UUID) -> str:
        return f"{created_at.isoformat()}|{message_id}"

    def _decode_cursor(self, cursor: str) -> tuple[datetime, uuid.UUID]:
        try:
            ts, msg_id = cursor.split("|", 1)
            return datetime.fromisoformat(ts), uuid.UUID(msg_id)
        except (ValueError, TypeError) as exc:
            raise AppError("invalid_cursor", "Invalid pagination cursor", status_code=400) from exc

    async def set_presence(self, redis: Redis, *, room_id: uuid.UUID, user_id: uuid.UUID) -> None:
        key = presence_key(room_id)
        now = datetime.now(UTC).isoformat()
        await redis.hset(key, str(user_id), now)
        await redis.expire(key, PRESENCE_TTL_SECONDS * 10)

    async def clear_presence(self, redis: Redis, *, room_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await redis.hdel(presence_key(room_id), str(user_id))

    async def get_presence(self, redis: Redis, *, room_id: uuid.UUID) -> list[str]:
        data = await redis.hgetall(presence_key(room_id))
        cutoff = datetime.now(UTC).timestamp() - PRESENCE_TTL_SECONDS
        active: list[str] = []
        for user_id, ts in data.items():
            try:
                seen = datetime.fromisoformat(ts).timestamp()
            except ValueError:
                continue
            if seen >= cutoff:
                active.append(user_id)
        return active

    async def set_typing(self, redis: Redis, *, room_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await redis.set(typing_key(room_id, user_id), "1", ex=TYPING_TTL_SECONDS)

    async def clear_typing(self, redis: Redis, *, room_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await redis.delete(typing_key(room_id, user_id))

    async def get_typing_users(self, redis: Redis, *, room_id: uuid.UUID) -> list[str]:
        pattern = f"chat:typing:{room_id}:*"
        users: list[str] = []
        async for key in redis.scan_iter(match=pattern):
            suffix = key.rsplit(":", 1)[-1]
            users.append(suffix)
        return users

    async def set_read_status(
        self,
        redis: Redis,
        *,
        room_id: uuid.UUID,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> None:
        await redis.set(read_key(room_id, user_id), str(message_id))

    async def get_read_status(self, redis: Redis, *, room_id: uuid.UUID, user_id: uuid.UUID) -> str | None:
        return await redis.get(read_key(room_id, user_id))

    async def subscribe_room(self, redis: Redis, room_id: uuid.UUID) -> AsyncIterator[dict[str, Any]]:
        pubsub = redis.pubsub()
        await pubsub.subscribe(room_channel(room_id))
        try:
            async for raw in pubsub.listen():
                if raw["type"] != "message":
                    continue
                data = raw["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield json.loads(data)
        finally:
            await pubsub.unsubscribe(room_channel(room_id))
            await pubsub.close()


chat_service = ChatService()
