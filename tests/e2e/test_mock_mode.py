"""E2E #14: Mock mode — no external API keys required."""

import os

import pytest


REQUIRED_MOCK_DEFAULTS = {
    "LLM_PROVIDER": "mock",
    "AUDIO_PROVIDER": "mock",
    "PAYMENT_PROVIDER": "mock",
}


@pytest.mark.e2e
def test_health_without_external_api_keys(client):
    """Stack must boot with mock providers (docker-compose default)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.e2e
def test_dev_login_without_api_keys(client):
    resp = client.post("/api/v1/auth/dev-login", json={"email": "artist@example.com"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["tokens"]


@pytest.mark.e2e
def test_mock_oauth_without_api_keys(client):
    resp = client.get("/api/v1/auth/oauth/mock/start")
    assert resp.status_code == 200
    assert resp.json()["provider"] == "mock"


@pytest.mark.e2e
def test_mock_provider_defaults():
    """MVP docker-compose uses mock providers — no vendor keys required."""
    for key, default in REQUIRED_MOCK_DEFAULTS.items():
        assert os.getenv(key, default) == default
