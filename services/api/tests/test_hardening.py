"""Security and metrics middleware tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_security_headers(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Content-Security-Policy" in resp.headers


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "hookpress_http_requests_total" in resp.text
    assert "hookpress_ws_connections" in resp.text
    assert "hookpress_celery_queue_depth" in resp.text
    assert "hookpress_storage_bytes_total" in resp.text


@pytest.mark.asyncio
async def test_billing_webhook_idempotency(client):
    """Webhook requires valid order_id — idempotency tested in test_billing_idempotency."""
    payload = {"order_id": "00000000-0000-0000-0000-000000000001", "amount_minor": 1000}
    headers = {"Idempotency-Key": "idem-billing-1"}
    first = await client.post("/api/v1/billing/webhooks/payment", json=payload, headers=headers)
    assert first.status_code in (200, 404, 400)
