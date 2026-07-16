"""E2E #7: Duplicate payment webhook must not double-charge."""

import uuid

import pytest

from conftest import buyer_headers


def _create_paid_order(client, buyer_headers) -> tuple[str, int]:
    search = client.get("/api/v1/market/kworks", params={"q": "Сведение"})
    if search.status_code != 200 or not search.json():
        pytest.skip("No seeded kworks")
    kwork_id = search.json()[0]["id"]

    order = client.post(
        "/api/v1/market/orders",
        headers=buyer_headers,
        json={"kwork_id": kwork_id},
    )
    if order.status_code == 400:
        pytest.skip("Cannot order own kwork — set HOOKPRESS_BUYER_EMAIL=admin@example.com")
    assert order.status_code == 200, order.text
    order_id = order.json()["id"]
    amount_minor = order.json()["amount_minor"]
    return order_id, amount_minor


@pytest.mark.e2e
def test_billing_webhook_idempotency(client, buyer_headers):
    order_id, amount_minor = _create_paid_order(client, buyer_headers)
    idem_key = f"idem_{uuid.uuid4().hex[:12]}"
    payload = {"order_id": order_id, "amount_minor": amount_minor}
    headers = {"Idempotency-Key": idem_key}

    first = client.post("/api/v1/billing/webhooks/payment", json=payload, headers=headers)
    second = client.post("/api/v1/billing/webhooks/payment", json=payload, headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert first.json()["status"] == "FUNDS_HELD"
    assert second.json()["status"] == "FUNDS_HELD"


@pytest.mark.e2e
def test_billing_webhook_requires_idempotency_key(client, buyer_headers):
    order_id, amount_minor = _create_paid_order(client, buyer_headers)
    resp = client.post(
        "/api/v1/billing/webhooks/payment",
        json={"order_id": order_id, "amount_minor": amount_minor},
    )
    assert resp.status_code == 422
