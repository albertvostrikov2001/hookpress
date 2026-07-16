"""Redis client."""

from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def ping_redis() -> bool:
    try:
        return await redis_client.ping()
    except Exception:
        return False
