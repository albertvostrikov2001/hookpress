"""Test fixtures."""

import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import engine
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def redis_client_per_test():
    import app.core.redis as redis_module

    client = Redis.from_url(settings.redis_url, decode_responses=True)
    previous = redis_module.redis_client
    redis_module.redis_client = client
    yield client
    await client.aclose()
    redis_module.redis_client = previous


@pytest.fixture(autouse=True)
async def dispose_db_connections():
    yield
    await engine.dispose()
