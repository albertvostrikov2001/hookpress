"""Integration: chat presence keys in Redis."""

import uuid

import pytest
from redis.asyncio import Redis

from app.application.chat_service import chat_service, presence_key
from app.core.config import settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_presence_roundtrip(require_redis):
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()
    await chat_service.set_presence(redis, room_id=room_id, user_id=user_id)
    online = await chat_service.get_presence(redis, room_id=room_id)
    assert str(user_id) in online
    await chat_service.clear_presence(redis, room_id=room_id, user_id=user_id)
    await redis.delete(presence_key(room_id))
    await redis.aclose()
