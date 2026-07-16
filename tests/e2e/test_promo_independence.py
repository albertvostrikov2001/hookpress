"""E2E #13: Core catalog/health independent of promo service."""

import pytest


@pytest.mark.e2e
def test_health_ok_without_promo(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "api"


@pytest.mark.e2e
def test_feed_articles_available_without_promo(client):
    resp = client.get("/api/v1/feed/articles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.e2e
def test_market_catalog_available_without_promo(client):
    resp = client.get("/api/v1/market/kworks")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.e2e
def test_promo_proxy_fails_gracefully(client, auth_headers):
    """Promo routes may 502 when Go service is down; core API stays healthy."""
    resp = client.get("/api/v1/promotions/campaigns", headers=auth_headers)
    assert resp.status_code in {200, 403, 502}
    health = client.get("/health")
    assert health.status_code == 200
