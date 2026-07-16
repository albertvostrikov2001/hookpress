"""Phase 3 endpoints: feed comments, distribution jobs, profile detail, dispute by order."""

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
async def test_list_feed_comments(client):
    headers = await _auth_headers(client)
    articles = await client.get("/api/v1/feed/articles")
    if not articles.json().get("items"):
        pytest.skip("No published articles")
    article_id = articles.json()["items"][0]["id"]

    post = await client.post(
        f"/api/v1/feed/articles/{article_id}/comments",
        headers=headers,
        json={"body": "Great read"},
    )
    assert post.status_code == 200

    listed = await client.get(f"/api/v1/feed/articles/{article_id}/comments")
    assert listed.status_code == 200
    bodies = [c["body"] for c in listed.json()]
    assert "Great read" in bodies


@pytest.mark.asyncio
async def test_get_chart_source(client):
    resp = await client.get("/api/v1/charts/sources/demo-top-40")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "demo-top-40"


@pytest.mark.asyncio
async def test_get_kwork_profile_detail(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "Profile Test",
            "description": "Detail",
            "price_minor": 50_000,
            "category": "design",
        },
    )
    assert created.status_code == 200
    profile_id = created.json()["profile_id"]

    detail = await client.get(f"/api/v1/market/profiles/{profile_id}")
    assert detail.status_code == 200
    assert "kworks" in detail.json()
