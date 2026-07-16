"""Chat message cursor pagination tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_message_cursor_pagination(client):
    headers = await _auth_headers(client)
    room = await client.post(
        "/api/v1/chat/rooms",
        headers=headers,
        json={"name": "Cursor room", "member_ids": []},
    )
    room_id = room.json()["id"]

    for i in range(3):
        await client.post(
            f"/api/v1/chat/rooms/{room_id}/messages",
            headers=headers,
            json={"body": f"msg-{i}", "client_message_id": str(uuid.uuid4())},
        )

    page1 = await client.get(
        f"/api/v1/chat/rooms/{room_id}/messages",
        headers=headers,
        params={"limit": 2},
    )
    assert page1.status_code == 200
    data = page1.json()
    assert len(data["items"]) == 2
    assert data["has_more"] is True
    assert data["next_cursor"]

    page2 = await client.get(
        f"/api/v1/chat/rooms/{room_id}/messages",
        headers=headers,
        params={"limit": 2, "cursor": data["next_cursor"]},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) >= 1
