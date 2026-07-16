"""Chat Redis pub/sub integration tests."""

import json
import uuid
from unittest.mock import MagicMock

import pytest

from app.application.chat_service import chat_service, room_channel


class FakePubSub:
    def __init__(self, messages: list[dict]):
        self._messages = [{"type": "subscribe", "data": 1}] + [
            {"type": "message", "data": json.dumps(m)} for m in messages
        ]
        self._index = 0
        self.subscribed: list[str] = []

    async def subscribe(self, channel: str):
        self.subscribed.append(channel)

    async def unsubscribe(self, channel: str):
        pass

    async def close(self):
        pass

    def listen(self):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._messages):
            raise StopAsyncIteration
        msg = self._messages[self._index]
        self._index += 1
        return msg


@pytest.mark.asyncio
async def test_room_channel_format():
    room_id = uuid.uuid4()
    assert room_channel(room_id) == f"chat:room:{room_id}"


@pytest.mark.asyncio
async def test_subscribe_room_yields_published_messages():
    room_id = uuid.uuid4()
    payload = {
        "id": str(uuid.uuid4()),
        "room_id": str(room_id),
        "sender_id": str(uuid.uuid4()),
        "client_message_id": "msg-1",
        "body": "Hello",
        "created_at": "2026-07-14T12:00:00+00:00",
    }

    fake_pubsub = FakePubSub([payload])
    redis = MagicMock()
    redis.pubsub = MagicMock(return_value=fake_pubsub)

    events = []
    async for event in chat_service.subscribe_room(redis, room_id):
        events.append(event)
        break

    assert events == [payload]
    assert fake_pubsub.subscribed == [room_channel(room_id)]
