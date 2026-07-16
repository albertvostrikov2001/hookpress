"""Auth flow tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.csrf_helpers import cookie_auth_from_login

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_dev_login_and_me(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    assert login.status_code == 200, login.text
    body = login.json()
    assert body["user"]["email"] == DEV_EMAIL
    assert "artist" in body["user"]["roles"]
    token = body["tokens"]["access_token"]

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == DEV_EMAIL


@pytest.mark.asyncio
async def test_refresh_rotation(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    refresh = login.cookies.get("hookpress_refresh")
    assert refresh
    cookies, headers = cookie_auth_from_login(login)

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        cookies=cookies,
        headers=headers,
    )
    assert refreshed.status_code == 200
    new_refresh = refreshed.cookies.get("hookpress_refresh")
    assert new_refresh
    assert new_refresh != refresh

    reuse = await client.post(
        "/api/v1/auth/refresh",
        cookies={"hookpress_refresh": refresh, **{k: v for k, v in cookies.items() if k != "hookpress_refresh"}},
        headers=headers,
    )
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_admin_forbidden_for_artist(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    resp = await client.get("/api/v1/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
