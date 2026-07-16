"""OAuth flow tests."""

import uuid
from urllib.parse import parse_qs, urlparse

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
async def test_mock_oauth_start_returns_redirect_url(client):
    resp = await client.get("/api/v1/auth/oauth/mock/start")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["redirect_url"].startswith("http://mock-oauth.test/authorize?")
    parsed = urlparse(body["redirect_url"])
    params = parse_qs(parsed.query)
    assert "state" in params


@pytest.mark.asyncio
async def test_mock_oauth_callback_creates_session(client):
    start = await client.get("/api/v1/auth/oauth/mock/start")
    assert start.status_code == 200
    redirect_url = start.json()["redirect_url"]
    state = parse_qs(urlparse(redirect_url).query)["state"][0]

    email = f"oauth-{uuid.uuid4().hex[:8]}@example.com"
    code = f"mock:{email}:OAuth Test User:sub-{uuid.uuid4().hex[:8]}"
    callback = await client.get(
        "/api/v1/auth/oauth/mock/callback",
        params={"code": code, "state": state},
    )
    assert callback.status_code == 200, callback.text
    body = callback.json()
    assert body["user"]["email"] == email
    assert "artist" in body["user"]["roles"]
    assert callback.cookies.get("hookpress_refresh")

    token = body["tokens"]["access_token"]
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_mock_oauth_links_existing_user_by_email(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")

    start = await client.get("/api/v1/auth/oauth/mock/start")
    state = parse_qs(urlparse(start.json()["redirect_url"]).query)["state"][0]
    code = f"mock:{DEV_EMAIL}:Linked Artist:linked-subject-1"

    callback = await client.get(
        "/api/v1/auth/oauth/mock/callback",
        params={"code": code, "state": state},
    )
    assert callback.status_code == 200, callback.text
    assert callback.json()["user"]["email"] == DEV_EMAIL
    assert callback.json()["user"]["id"] == login.json()["user"]["id"]


@pytest.mark.asyncio
async def test_unconfigured_oauth_provider_returns_501(client):
    resp = await client.get("/api/v1/auth/oauth/google/start")
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "oauth_not_configured"
