"""Phase 2 read endpoints: kwork detail, my orders, chat rooms, wallet ledger."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_kwork_by_id(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "Mix Master",
            "description": "Full mix",
            "price_minor": 120_000,
            "category": "production",
        },
    )
    assert created.status_code == 200
    kwork_id = created.json()["id"]
    await client.post(f"/api/v1/market/kworks/{kwork_id}/publish", headers=headers)

    detail = await client.get(f"/api/v1/market/kworks/{kwork_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == kwork_id
    assert detail.json()["title"] == "Mix Master"


@pytest.mark.asyncio
async def test_list_my_orders(client):
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/market/orders/mine", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_chat_rooms(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/chat/rooms",
        headers=headers,
        json={"name": "Test room", "member_ids": []},
    )
    assert created.status_code == 200

    listed = await client.get("/api/v1/chat/rooms", headers=headers)
    assert listed.status_code == 200
    ids = [r["id"] for r in listed.json()]
    assert created.json()["id"] in ids


@pytest.mark.asyncio
async def test_list_wallet_entries(client):
    headers = await _auth_headers(client)
    resp = await client.get("/api/v1/billing/wallet/entries", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
