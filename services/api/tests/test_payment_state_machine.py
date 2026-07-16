"""Payment provider state machine tests."""

import pytest

from app.infrastructure.providers.payment import MockPaymentProvider


@pytest.mark.asyncio
async def test_mock_payment_create_and_capture():
    provider = MockPaymentProvider()
    intent = await provider.create_payment(
        order_id="order-1",
        amount_minor=5000,
        idempotency_key="pay-key-1",
    )
    assert intent.status == "pending"
    assert intent.internal_status == "PENDING"

    captured = await provider.parse_webhook(
        {
            "idempotency_key": "pay-key-1",
            "amount_minor": 5000,
            "order_id": "order-1",
        }
    )
    assert captured.status == "succeeded"
    assert captured.internal_status == "CAPTURED"
