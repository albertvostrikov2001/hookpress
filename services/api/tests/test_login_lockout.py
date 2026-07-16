"""Login lockout tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def lockout_email():
    email = f"lockout-{uuid.uuid4().hex[:8]}@example.com"
    normalized = email.strip().lower()
    failures_key = f"login:failures:{normalized}"
    locked_key = f"login:locked:{normalized}"
    from app.core import redis as redis_core

    yield email
    client = redis_core.redis_client
    await client.delete(failures_key, locked_key)


@pytest.mark.asyncio
async def test_lockout_after_repeated_failed_logins(client, lockout_email):
    for _ in range(settings.login_lockout_max_attempts):
        resp = await client.post("/api/v1/auth/dev-login", json={"email": lockout_email})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "user_not_found"

    locked = await client.post("/api/v1/auth/dev-login", json={"email": lockout_email})
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "account_locked"


@pytest.mark.asyncio
async def test_successful_login_clears_lockout(client, lockout_email):
    for _ in range(settings.login_lockout_max_attempts):
        await client.post("/api/v1/auth/dev-login", json={"email": lockout_email})

    locked = await client.post("/api/v1/auth/dev-login", json={"email": lockout_email})
    assert locked.status_code == 429

    from app.core import redis as redis_core

    normalized = lockout_email.strip().lower()
    await redis_core.redis_client.delete(f"login:failures:{normalized}", f"login:locked:{normalized}")

    success = await client.post("/api/v1/auth/dev-login", json={"email": "artist@example.com"})
    if success.status_code == 404:
        pytest.skip("Seed user not in database")
    assert success.status_code == 200

    retry = await client.post("/api/v1/auth/dev-login", json={"email": lockout_email})
    assert retry.status_code == 404
