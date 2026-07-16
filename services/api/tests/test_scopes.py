"""RBAC scope enforcement tests."""

import pytest
from httpx import AsyncClient

MODERATOR_EMAIL = "moderator@example.com"
DEV_EMAIL = "artist@example.com"


async def _auth_headers(client: AsyncClient, email: str) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": email})
    if login.status_code == 404:
        pytest.skip("Dev login disabled or user not seeded")
    assert login.status_code == 200, login.text
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_moderator_can_read_studio_projects(client: AsyncClient):
    headers = await _auth_headers(client, MODERATOR_EMAIL)
    response = await client.get("/api/v1/studio/projects", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_moderator_cannot_create_studio_project(client: AsyncClient):
    headers = await _auth_headers(client, MODERATOR_EMAIL)
    response = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Scope test project"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


@pytest.mark.asyncio
async def test_moderator_cannot_create_market_kwork(client: AsyncClient):
    headers = await _auth_headers(client, MODERATOR_EMAIL)
    response = await client.post(
        "/api/v1/market/kworks",
        json={
            "title": "Scope test kwork",
            "description": "Should be denied",
            "price_minor": 1000,
            "category": "design",
        },
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_artist_can_create_studio_project(client: AsyncClient):
    headers = await _auth_headers(client, DEV_EMAIL)
    response = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Artist scope test"},
        headers=headers,
    )
    assert response.status_code == 201
