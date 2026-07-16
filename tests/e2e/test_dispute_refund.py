"""E2E #6: Dispute with partial refund."""

import uuid

import pytest


def _find_seeded_kwork(client) -> str | None:
    search = client.get("/api/v1/market/kworks", params={"q": "Сведение"})
    if search.status_code != 200:
        return None
    items = search.json()
    return items[0]["id"] if items else None


def _fund_order(client, buyer_headers, auth_headers) -> tuple[str, int]:
    kwork_id = _find_seeded_kwork(client)
    if not kwork_id:
        pytest.skip("No seeded kworks found")

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

    idem = f"e2e-dispute-{uuid.uuid4()}"
    client.post(
        f"/api/v1/billing/orders/{order_id}/pay",
        headers={**buyer_headers, "Idempotency-Key": idem},
    )
    client.post(
        "/api/v1/billing/webhooks/payment",
        json={"order_id": order_id, "amount_minor": amount_minor},
        headers={"Idempotency-Key": idem},
    )
    client.post(
        f"/api/v1/market/orders/{order_id}/transition",
        headers=auth_headers,
        json={"to_status": "IN_PROGRESS"},
    )
    return order_id, amount_minor


@pytest.mark.e2e
def test_dispute_partial_refund(client, buyer_headers, auth_headers, admin_headers):
    order_id, amount_minor = _fund_order(client, buyer_headers, auth_headers)

    message = client.post(
        f"/api/v1/market/orders/{order_id}/messages",
        headers=buyer_headers,
        json={"body": "Quality concern on deliverable"},
    )
    assert message.status_code == 200, message.text

    dispute = client.post(
        f"/api/v1/disputes/orders/{order_id}",
        headers=buyer_headers,
        json={"reason": "Partial quality issues"},
    )
    assert dispute.status_code == 200, dispute.text
    dispute_id = dispute.json()["id"]
    assert dispute.json()["status"] == "OPEN"

    frozen = client.post(
        f"/api/v1/market/orders/{order_id}/messages",
        headers=buyer_headers,
        json={"body": "Should be blocked"},
    )
    assert frozen.status_code == 409
    assert frozen.json()["error"]["code"] == "messages_frozen"

    partial_refund = amount_minor // 2
    resolve = client.post(
        f"/api/v1/disputes/{dispute_id}/resolve",
        headers=admin_headers,
        json={
            "resolution": "50% refund approved",
            "refund_amount_minor": partial_refund,
        },
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["order"]["status"] == "PARTIALLY_REFUNDED"
    assert resolve.json()["dispute"]["status"] == "CLOSED"
