"""Promotions proxy tests."""

from unittest.mock import AsyncMock, patch

import httpx
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
async def test_list_campaigns_proxies_to_promo(client):
    headers = await _auth_headers(client)
    upstream_response = httpx.Response(
        200,
        json={"items": [{"id": "camp-1", "name": "Launch"}]},
        request=httpx.Request("GET", "http://promo:8081/api/v1/campaigns"),
    )

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=upstream_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.api.v1.promotions.httpx.AsyncClient", return_value=mock_client):
        resp = await client.get("/api/v1/promotions/campaigns", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == "camp-1"
    mock_client.request.assert_awaited_once()
    call_args = mock_client.request.await_args
    assert call_args.args[0] == "GET"
    assert call_args.kwargs["headers"]["Authorization"].startswith("Bearer ")


@pytest.mark.asyncio
async def test_create_campaign_forwards_auth(client):
    headers = await _auth_headers(client)
    upstream_response = httpx.Response(
        201,
        json={"id": "camp-2", "name": "Summer", "budget_cents": 1000},
        request=httpx.Request("POST", "http://promo:8081/api/v1/campaigns"),
    )

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=upstream_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    payload = {
        "name": "Summer",
        "budget_cents": 1000,
        "schedule": {"start_at": "2026-01-01T00:00:00Z", "end_at": "2026-12-31T00:00:00Z"},
    }
    with patch("app.api.v1.promotions.httpx.AsyncClient", return_value=mock_client):
        resp = await client.post("/api/v1/promotions/campaigns", headers=headers, json=payload)

    assert resp.status_code == 201
    assert resp.json()["id"] == "camp-2"
    call_args = mock_client.request.await_args
    assert call_args.args[0] == "POST"
    assert "Authorization" in call_args.kwargs["headers"]


@pytest.mark.asyncio
async def test_promo_unavailable_returns_502(client):
    headers = await _auth_headers(client)

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.api.v1.promotions.httpx.AsyncClient", return_value=mock_client):
        resp = await client.get("/api/v1/promotions/campaigns", headers=headers)

    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "promo_unavailable"
