"""Task event streaming via Redis pub/sub with in-memory fallback."""

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator

from app.core.redis import redis_client


class TaskEventBus:
    def __init__(self) -> None:
        self._memory_channels: dict[str, asyncio.Queue[str]] = defaultdict(asyncio.Queue)
        self._redis_available: bool | None = None

    async def _check_redis(self) -> bool:
        if self._redis_available is not None:
            return self._redis_available
        try:
            self._redis_available = await redis_client.ping()
        except Exception:
            self._redis_available = False
        return self._redis_available

    def channel_name(self, task_id: str) -> str:
        return f"task:{task_id}"

    async def publish(self, task_id: str, event: dict) -> None:
        payload = json.dumps(event)
        channel = self.channel_name(task_id)
        if await self._check_redis():
            await redis_client.publish(channel, payload)
        await self._memory_channels[channel].put(payload)

    async def subscribe(self, task_id: str) -> AsyncIterator[str]:
        channel = self.channel_name(task_id)
        if await self._check_redis():
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(channel)
            try:
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        data = message.get("data")
                        if isinstance(data, bytes):
                            yield data.decode()
                        else:
                            yield str(data)
                    else:
                        await asyncio.sleep(0.1)
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
        else:
            queue = self._memory_channels[channel]
            while True:
                yield await queue.get()


task_event_bus = TaskEventBus()
