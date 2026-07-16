"""Login history API tests."""

import pytest
from httpx import AsyncClient

DEV_EMAIL = "artist@example.com"


@pytest.mark.asyncio
async def test_login_events_after_dev_login(client: AsyncClient):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Dev login disabled or user not seeded")
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}

    events = await client.get("/api/v1/users/me/login-events", headers=headers)
    assert events.status_code == 200
    body = events.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["success"] is True
    assert body[0]["method"] == "dev_login"
