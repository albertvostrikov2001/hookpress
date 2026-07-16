"""Shared fixtures for E2E tests against localhost:8000."""

import os

import httpx
import pytest

# 127.0.0.1 avoids Windows proxy intercepting localhost (503 via proxy-connection)
BASE_URL = os.getenv("HOOKPRESS_API_URL", "http://127.0.0.1:8000")
DEV_EMAIL = os.getenv("HOOKPRESS_DEV_EMAIL", "artist@example.com")
ADMIN_EMAIL = os.getenv("HOOKPRESS_ADMIN_EMAIL", "admin@example.com")
BUYER_EMAIL = os.getenv("HOOKPRESS_BUYER_EMAIL", ADMIN_EMAIL)


def _http_client(**kwargs) -> httpx.Client:
    """HTTP client that bypasses system proxy for local Docker ports."""
    return httpx.Client(trust_env=False, **kwargs)


def cookie_auth_from_response(response: httpx.Response) -> tuple[dict[str, str], dict[str, str]]:
    """Build cookie-auth headers for CSRF-protected refresh/logout routes."""
    refresh = response.cookies.get("hookpress_refresh")
    csrf = response.cookies.get("hookpress_csrf")
    cookies: dict[str, str] = {}
    if refresh:
        cookies["hookpress_refresh"] = refresh
    if csrf:
        cookies["hookpress_csrf"] = csrf
    headers = {"X-CSRF-Token": csrf} if csrf else {}
    return cookies, headers


def dev_login(client: httpx.Client, email: str = DEV_EMAIL) -> tuple[dict[str, str], httpx.Response]:
    """Dev-login and return bearer headers plus the raw response (cookies for refresh)."""
    client.get("/health")
    resp = client.post("/api/v1/auth/dev-login", json={"email": email})
    if resp.status_code == 404:
        pytest.skip(f"User {email} not seeded — run scripts/seed.py")
    assert resp.status_code == 200, resp.text
    token = resp.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, resp


@pytest.fixture(scope="session")
def api_available():
    try:
        with _http_client(base_url=BASE_URL, timeout=5.0) as client:
            resp = client.get("/health")
            return resp.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture
def client(api_available):
    if not api_available:
        pytest.skip(f"API not reachable at {BASE_URL}")
    with _http_client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    headers, _ = dev_login(client, DEV_EMAIL)
    return headers


@pytest.fixture
def admin_headers(client):
    headers, _ = dev_login(client, ADMIN_EMAIL)
    return headers


@pytest.fixture
def buyer_headers(client):
    headers, _ = dev_login(client, BUYER_EMAIL)
    return headers
