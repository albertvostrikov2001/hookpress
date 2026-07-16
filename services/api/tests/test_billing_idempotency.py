"""Billing idempotency tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.application.billing_service import billing_service
from app.core.database import SessionLocal
from app.infrastructure.models.ledger_entry import LedgerEntry
from app.infrastructure.models.user import User
from app.infrastructure.providers.payment import MockPaymentProvider
from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_ledger_double_entry_idempotent():
    provider = MockPaymentProvider()
    idem = f"test-hold-{uuid.uuid4()}"

    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            pytest.skip("Seed user not in database")

        await billing_service.credit_wallet(
            db,
            user_id=user.id,
            amount_minor=10_000,
            idempotency_key=f"{idem}:topup",
            description="Test top-up",
        )
        order_id = uuid.uuid4()
        first = await billing_service.hold_funds(
            db,
            buyer_id=user.id,
            order_id=order_id,
            amount_minor=5_000,
            idempotency_key=idem,
        )
        second = await billing_service.hold_funds(
            db,
            buyer_id=user.id,
            order_id=order_id,
            amount_minor=5_000,
            idempotency_key=idem,
        )
        await db.commit()

    assert len(first) == 2
    assert len(second) == 2
    assert first[0].transaction_id == second[0].transaction_id

    async with SessionLocal() as db:
        result = await db.execute(select(LedgerEntry).where(LedgerEntry.idempotency_key == f"{idem}:0"))
        entries = list(result.scalars().all())
        assert len(entries) == 1


@pytest.mark.asyncio
async def test_payment_webhook_idempotent(client):
    headers = await _auth_headers(client)
    kwork = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "Test Mix",
            "description": "Professional mix",
            "price_minor": 150_000,
            "category": "sound_engineering",
        },
    )
    assert kwork.status_code == 200, kwork.text
    kwork_id = kwork.json()["id"]
    publish = await client.post(f"/api/v1/market/kworks/{kwork_id}/publish", headers=headers)
    assert publish.status_code == 200

    order = await client.post(
        "/api/v1/market/orders",
        headers=headers,
        json={"kwork_id": kwork_id},
    )
    if order.status_code == 400:
        pytest.skip("Cannot order own kwork with single seed user")
    assert order.status_code == 200, order.text
    order_id = order.json()["id"]
    idem = f"wh-{uuid.uuid4()}"

    payload = {"order_id": order_id, "amount_minor": order.json()["amount_minor"]}
    first = await client.post(
        "/api/v1/billing/webhooks/payment",
        json=payload,
        headers={"Idempotency-Key": idem},
    )
    second = await client.post(
        "/api/v1/billing/webhooks/payment",
        json=payload,
        headers={"Idempotency-Key": idem},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["status"] == "FUNDS_HELD"
    assert second.json()["status"] == "FUNDS_HELD"
