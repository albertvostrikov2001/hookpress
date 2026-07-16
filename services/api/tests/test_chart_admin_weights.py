"""Admin chart weight PATCH tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

ADMIN_EMAIL = "admin@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _admin_headers(client: AsyncClient) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": ADMIN_EMAIL})
    if login.status_code == 404:
        pytest.skip("Admin user not seeded")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_update_chart_weights(client):
    headers = await _admin_headers(client)
    response = await client.patch(
        "/api/v1/admin/charts/sources/demo-top-40/weights",
        headers=headers,
        json={"weights": {"streams": 0.5, "downloads": 0.3, "social": 0.1, "editorial": 0.1}},
    )
    assert response.status_code == 200, response.text
    weights = response.json()["source_weights"]
    assert abs(sum(weights.values()) - 1.0) < 0.01


@pytest.mark.asyncio
async def test_non_admin_cannot_update_chart_weights(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": "artist@example.com"})
    if login.status_code == 404:
        pytest.skip("Artist user not seeded")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}
    response = await client.patch(
        "/api/v1/admin/charts/sources/demo-top-40/weights",
        headers=headers,
        json={"weights": {"streams": 1.0}},
    )
    assert response.status_code == 403
