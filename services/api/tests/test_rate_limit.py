"""Rate limiting middleware tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_requests", 3)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client):
    path = "/api/v1/charts/demo-top-40"
    for _ in range(3):
        ok = await client.get(path)
        assert ok.status_code in {200, 404}
    blocked = await client.get(path)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limit_exceeded"
