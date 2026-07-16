"""E2E #5: Kwork order escrow — pay (Idempotency-Key required) and capture."""

import uuid

import pytest


def _find_seeded_kwork(client) -> str | None:
    search = client.get("/api/v1/market/kworks", params={"q": "Сведение"})
    if search.status_code != 200:
        return None
    items = search.json()
    return items[0]["id"] if items else None


@pytest.mark.e2e
def test_pay_requires_idempotency_key(client, buyer_headers):
    missing = client.post(
        f"/api/v1/billing/orders/{uuid.uuid4()}/pay",
        headers=buyer_headers,
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "idempotency_required"


@pytest.mark.e2e
def test_kwork_escrow_pay_and_capture(client, buyer_headers, auth_headers, admin_headers):
    kwork_id = _find_seeded_kwork(client)
    if not kwork_id:
        pytest.skip("No seeded kworks found")

    order = client.post(
        "/api/v1/market/orders",
        headers=buyer_headers,
        json={"kwork_id": kwork_id},
    )
    if order.status_code == 400 and order.json()["error"]["code"] == "cannot_order_own_kwork":
        pytest.skip("Buyer and seller are the same user — set HOOKPRESS_BUYER_EMAIL=admin@example.com")
    assert order.status_code == 200, order.text
    order_id = order.json()["id"]
    amount_minor = order.json()["amount_minor"]

    idem = f"e2e-pay-{uuid.uuid4()}"
    pay = client.post(
        f"/api/v1/billing/orders/{order_id}/pay",
        headers={**buyer_headers, "Idempotency-Key": idem},
    )
    assert pay.status_code == 200, pay.text
    assert pay.json()["idempotency_key"] == idem

    webhook = client.post(
        "/api/v1/billing/webhooks/payment",
        json={"order_id": order_id, "amount_minor": amount_minor},
        headers={"Idempotency-Key": idem},
    )
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()["status"] == "FUNDS_HELD"
    assert webhook.json()["duplicate"] is False

    in_progress = client.post(
        f"/api/v1/market/orders/{order_id}/transition",
        headers=auth_headers,
        json={"to_status": "IN_PROGRESS"},
    )
    assert in_progress.status_code == 200, in_progress.text

    delivered = client.post(
        f"/api/v1/market/orders/{order_id}/transition",
        headers=auth_headers,
        json={"to_status": "DELIVERED"},
    )
    assert delivered.status_code == 200, delivered.text

    capture = client.post(
        f"/api/v1/billing/orders/{order_id}/capture",
        headers={**admin_headers, "Idempotency-Key": f"capture-{order_id}"},
    )
    assert capture.status_code == 200, capture.text
    assert capture.json()["status"] == "COMPLETED"
