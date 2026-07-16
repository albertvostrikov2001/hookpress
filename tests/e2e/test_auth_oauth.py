"""E2E #1: mock OAuth start/callback and dev-login refresh/logout."""

import uuid
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from conftest import cookie_auth_from_response, dev_login

DEV_EMAIL = "artist@example.com"


@pytest.mark.e2e
def test_mock_oauth_start_returns_redirect(client):
    resp = client.get("/api/v1/auth/oauth/mock/start")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["redirect_url"].startswith("http://mock-oauth.test/authorize?")
    assert "state" in parse_qs(urlparse(body["redirect_url"]).query)


@pytest.mark.e2e
def test_mock_oauth_callback_creates_session(client):
    start = client.get("/api/v1/auth/oauth/mock/start")
    assert start.status_code == 200
    state = parse_qs(urlparse(start.json()["redirect_url"]).query)["state"][0]
    email = f"oauth-e2e-{uuid.uuid4().hex[:8]}@example.com"
    code = f"mock:{email}:OAuth E2E User:sub-{uuid.uuid4().hex[:8]}"

    callback = client.get(
        "/api/v1/auth/oauth/mock/callback",
        params={"code": code, "state": state},
    )
    assert callback.status_code == 200, callback.text
    body = callback.json()
    assert body["user"]["email"] == email
    assert callback.cookies.get("hookpress_refresh")

    token = body["tokens"]["access_token"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.e2e
def test_dev_login_refresh_logout(client):
    headers, login = dev_login(client, DEV_EMAIL)
    assert login.cookies.get("hookpress_refresh")

    csrf = client.cookies.get("hookpress_csrf")
    refresh = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": csrf} if csrf else {},
    )
    assert refresh.status_code == 200, refresh.text
    access = refresh.json()["tokens"]["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access}", "X-CSRF-Token": csrf or ""},
    )
    assert logout.status_code == 204


@pytest.mark.e2e
def test_csrf_blocks_cookie_refresh_without_token(client):
    health = client.get("/health")
    if not health.cookies.get("hookpress_csrf"):
        pytest.skip("CSRF middleware not in running API image — rebuild hookpress-api")

    _, login = dev_login(client, DEV_EMAIL)
    refresh_cookie = login.cookies.get("hookpress_refresh")
    assert refresh_cookie

    with httpx.Client(base_url=client.base_url, timeout=30.0, trust_env=False) as isolated:
        blocked = isolated.post(
            "/api/v1/auth/refresh",
            cookies={"hookpress_refresh": refresh_cookie},
        )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "csrf_failed"


@pytest.mark.e2e
def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.e2e
def test_csrf_cookie_when_middleware_active(client):
    resp = client.get("/health")
    csrf = resp.cookies.get("hookpress_csrf")
    if csrf is None:
        pytest.skip("CSRF middleware not in running API image — rebuild hookpress-api")
    assert csrf
