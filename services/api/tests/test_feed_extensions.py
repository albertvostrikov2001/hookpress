"""Feed bookmarks, views, and moderation tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

DEV_EMAIL = "artist@example.com"
ADMIN_EMAIL = "admin@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient, email: str = DEV_EMAIL) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": email})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_bookmark_toggle(client):
    headers = await _auth_headers(client)
    suffix = uuid.uuid4().hex[:8]
    article = await client.post(
        "/api/v1/feed/articles",
        headers=headers,
        json={"title": f"Bookmark test {suffix}", "body": "content"},
    )
    if article.status_code == 401:
        pytest.skip("Auth unavailable")
    article_id = article.json()["id"]

    first = await client.post(f"/api/v1/feed/articles/{article_id}/bookmark", headers=headers)
    assert first.status_code == 200
    assert first.json()["bookmarked"] is True

    second = await client.post(f"/api/v1/feed/articles/{article_id}/bookmark", headers=headers)
    assert second.json()["bookmarked"] is False


@pytest.mark.asyncio
async def test_view_count(client):
    headers = await _auth_headers(client)
    suffix = uuid.uuid4().hex[:8]
    article = await client.post(
        "/api/v1/feed/articles",
        headers=headers,
        json={"title": f"View test {suffix}", "body": "content"},
    )
    article_id = article.json()["id"]

    view = await client.post(f"/api/v1/feed/articles/{article_id}/view", headers=headers)
    assert view.status_code == 200
    assert view.json()["view_count"] >= 1


@pytest.mark.asyncio
async def test_moderation_approve(client):
    author_headers = await _auth_headers(client)
    admin_headers = await _auth_headers(client, ADMIN_EMAIL)
    suffix = uuid.uuid4().hex[:8]

    article = await client.post(
        "/api/v1/feed/articles",
        headers=author_headers,
        json={"title": f"Moderation test {suffix}", "body": "content"},
    )
    article_id = article.json()["id"]
    assert article.json()["moderation_status"] == "PENDING"

    approved = await client.post(
        f"/api/v1/admin/feed/articles/{article_id}/approve",
        headers=admin_headers,
    )
    if approved.status_code == 403:
        pytest.skip("Admin user not seeded")
    assert approved.status_code == 200
    assert approved.json()["moderation_status"] == "APPROVED"


@pytest.mark.asyncio
async def test_rss_ingest_blocks_private_url(client):
    headers = await _auth_headers(client)
    resp = await client.post(
        "/api/v1/feed/ingest/rss",
        headers=headers,
        json={"feed_url": "http://127.0.0.1/rss.xml"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ssrf_blocked"
