"""
Cross-instance chat pub/sub integration test.

Requires Docker Compose with Redis and at least two API replicas for full
end-to-end verification:

    docker compose up -d --scale api=2

This test validates Redis relay semantics in-process using two concurrent
subscribers (simulating separate API instances connected to the same Redis).
"""

import asyncio
import json
import uuid

import pytest
from redis.asyncio import Redis

from app.application.chat_service import chat_service, room_channel
from app.core.config import settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_two_subscribers_receive_same_message(require_redis):
    """
    Two pub/sub consumers on the same room channel should both receive a
    published message — the mechanism used when `docker compose --scale api=2`.
    """
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    room_id = uuid.uuid4()
    channel = room_channel(room_id)
    payload = {
        "type": "message",
        "id": str(uuid.uuid4()),
        "room_id": str(room_id),
        "sender_id": str(uuid.uuid4()),
        "client_message_id": "integration-1",
        "body": "hello from instance A",
        "created_at": "2026-07-14T12:00:00+00:00",
    }

    received: list[dict] = []

    async def consume(label: str):
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            data = json.loads(raw["data"])
            received.append(data)
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            break

    task_a = asyncio.create_task(consume("a"))
    task_b = asyncio.create_task(consume("b"))
    await asyncio.sleep(0.05)
    await redis.publish(channel, json.dumps(payload))
    await asyncio.wait([task_a, task_b], timeout=2.0)

    assert len(received) == 2
    assert all(item["body"] == payload["body"] for item in received)
    await redis.aclose()
