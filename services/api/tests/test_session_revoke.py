"""Session revoke tests."""

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
async def test_revoke_single_session(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    refresh = login.cookies.get("hookpress_refresh")
    cookies, headers = cookie_auth_from_login(login)

    second = await client.post(
        "/api/v1/auth/refresh",
        cookies=cookies,
        headers=headers,
    )
    assert second.status_code == 200

    sessions = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions.status_code == 200
    active = sessions.json()
    assert len(active) >= 1
    session_id = active[0]["id"]

    revoke = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoke.status_code == 204

    sessions_after = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    remaining_ids = {item["id"] for item in sessions_after.json()}
    assert session_id not in remaining_ids


@pytest.mark.asyncio
async def test_revoke_all_sessions(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    refresh = login.cookies.get("hookpress_refresh")
    cookies, headers = cookie_auth_from_login(login)

    await client.post("/api/v1/auth/refresh", cookies=cookies, headers=headers)

    revoke_all = await client.post(
        "/api/v1/auth/sessions/revoke-all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoke_all.status_code == 204

    sessions = await client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions.status_code == 200
    assert sessions.json() == []

    refresh_after = await client.post(
        "/api/v1/auth/refresh",
        cookies={"hookpress_refresh": refresh, **{k: v for k, v in cookies.items() if k != "hookpress_refresh"}},
        headers=headers,
    )
    assert refresh_after.status_code == 401
