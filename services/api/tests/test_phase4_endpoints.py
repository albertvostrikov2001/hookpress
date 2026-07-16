"""Phase 4: feed categories/pagination, audit logs, kwork cover."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

ADMIN_EMAIL = "admin@example.com"
DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_feed_categories_and_pagination(client):
    cats = await client.get("/api/v1/feed/categories")
    assert cats.status_code == 200
    assert isinstance(cats.json(), list)

    page = await client.get("/api/v1/feed/articles", params={"limit": 5, "offset": 0})
    assert page.status_code == 200
    body = page.json()
    assert "items" in body
    assert "total" in body
    assert "has_more" in body


@pytest.mark.asyncio
async def test_admin_audit_logs(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": ADMIN_EMAIL})
    if login.status_code == 404:
        pytest.skip("Admin user not seeded")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}
    resp = await client.get("/api/v1/admin/audit-logs", headers=headers, params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_kwork_preview_url_not_found_without_cover(client):
    headers = {}
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}

    created = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "No Cover",
            "description": "Test",
            "price_minor": 40_000,
            "category": "design",
        },
    )
    kid = created.json()["id"]
    await client.post(f"/api/v1/market/kworks/{kid}/publish", headers=headers)

    preview = await client.get(f"/api/v1/market/kworks/{kid}/preview-url")
    assert preview.status_code == 404
