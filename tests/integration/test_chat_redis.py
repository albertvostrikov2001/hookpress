"""
E2E #9: Chat Redis pub/sub across instances.

Full cross-process WebSocket verification requires multiple API replicas:

    docker compose up -d --scale api=2
    export HOOKPRESS_MULTI_API=1
    pytest tests/integration/test_chat_redis.py -q

With a single API instance, the in-process Redis relay test below still validates
the pub/sub mechanism used for horizontal chat scaling.
"""

import asyncio
import json
import os
import uuid

import pytest
from redis.asyncio import Redis

from app.application.chat_service import chat_service, room_channel
from app.core.config import settings

pytestmark = pytest.mark.integration

MULTI_API = os.getenv("HOOKPRESS_MULTI_API", "").lower() in {"1", "true", "yes"}


@pytest.mark.asyncio
async def test_two_subscribers_receive_same_message(require_redis):
    """Two pub/sub consumers on the same channel (simulates --scale api=2)."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    room_id = uuid.uuid4()
    channel = room_channel(room_id)
    payload = {
        "type": "message",
        "id": str(uuid.uuid4()),
        "room_id": str(room_id),
        "sender_id": str(uuid.uuid4()),
        "client_message_id": "integration-redis-1",
        "body": "hello from instance A",
        "created_at": "2026-07-14T12:00:00+00:00",
    }

    received: list[dict] = []

    async def consume():
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

    task_a = asyncio.create_task(consume())
    task_b = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    await redis.publish(channel, json.dumps(payload))
    await asyncio.wait([task_a, task_b], timeout=2.0)

    assert len(received) == 2
    assert all(item["body"] == payload["body"] for item in received)
    await redis.aclose()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not MULTI_API,
    reason="Requires docker compose --scale api=2 (set HOOKPRESS_MULTI_API=1)",
)
async def test_chat_service_subscribe_across_instances(require_redis):
    """End-to-end relay when multiple API replicas share Redis."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    room_id = uuid.uuid4()
    payload = {
        "id": str(uuid.uuid4()),
        "room_id": str(room_id),
        "sender_id": str(uuid.uuid4()),
        "client_message_id": "multi-api-1",
        "body": "cross-instance relay",
        "created_at": "2026-07-14T12:00:00+00:00",
    }

    async def relay(label: str) -> dict:
        async for event in chat_service.subscribe_room(redis, room_id):
            return event
        raise AssertionError(f"no event on {label}")

    task_a = asyncio.create_task(relay("a"))
    task_b = asyncio.create_task(relay("b"))
    await asyncio.sleep(0.05)
    await redis.publish(room_channel(room_id), json.dumps(payload))
    done, pending = await asyncio.wait([task_a, task_b], timeout=2.0)
    for task in pending:
        task.cancel()

    assert len(done) == 2
    bodies = [t.result()["body"] for t in done]
    assert bodies == ["cross-instance relay", "cross-instance relay"]
    await redis.aclose()
