"""Phase 5: feed tags, kwork portfolio."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_feed_tags(client):
    resp = await client.get("/api/v1/feed/tags")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_feed_articles_tag_filter(client):
    page = await client.get("/api/v1/feed/articles", params={"tag": "nonexistent-tag", "limit": 5})
    assert page.status_code == 200
    assert page.json()["total"] == 0


@pytest.mark.asyncio
async def test_kwork_portfolio_urls_empty(client):
    headers = {}
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}

    created = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "Portfolio Test",
            "description": "Test",
            "price_minor": 40_000,
            "category": "design",
        },
    )
    kid = created.json()["id"]
    await client.post(f"/api/v1/market/kworks/{kid}/publish", headers=headers)

    urls = await client.get(f"/api/v1/market/kworks/{kid}/portfolio-urls")
    assert urls.status_code == 200
    assert urls.json()["items"] == []
