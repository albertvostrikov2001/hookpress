"""Security response header and CSRF smoke tests."""

import pytest

pytestmark = pytest.mark.security


@pytest.mark.asyncio
async def test_security_headers_on_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in resp.headers
    assert "Permissions-Policy" in resp.headers


@pytest.mark.asyncio
async def test_correlation_id_echoed(client):
    resp = await client.get("/health", headers={"X-Request-ID": "sec-test-corr"})
    assert resp.headers.get("X-Request-ID") == "sec-test-corr"


@pytest.mark.asyncio
async def test_csrf_cookie_issued_on_safe_request(client):
    resp = await client.get("/health")
    assert resp.cookies.get("hookpress_csrf")


@pytest.mark.asyncio
async def test_csrf_blocks_cookie_refresh_without_token(client):
    login = await client.post(
        "/api/v1/auth/dev-login",
        json={"email": "artist@example.com"},
    )
    assert login.status_code == 200
    refresh_cookie = login.cookies.get("hookpress_refresh")
    assert refresh_cookie

    blocked = await client.post(
        "/api/v1/auth/refresh",
        cookies={"hookpress_refresh": refresh_cookie},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "csrf_failed"


@pytest.mark.asyncio
async def test_csrf_allows_bearer_refresh(client):
    login = await client.post(
        "/api/v1/auth/dev-login",
        json={"email": "artist@example.com"},
    )
    refresh_cookie = login.cookies.get("hookpress_refresh")

    refreshed = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_cookie}"},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["tokens"]["access_token"]
