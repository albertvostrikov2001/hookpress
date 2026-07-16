"""HTTP idempotency dependency tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.application.idempotency_service import hash_request, idempotency_service
from app.core.database import SessionLocal
from app.infrastructure.models.idempotency_key import IdempotencyKey
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.market_order import MarketOrder
from app.infrastructure.models.user import User
from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient, email: str = DEV_EMAIL) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": email})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_pay_requires_idempotency_key(client):
    headers = await _auth_headers(client)
    resp = await client.post(f"/api/v1/billing/orders/{uuid.uuid4()}/pay", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "idempotency_required"


@pytest.mark.asyncio
async def test_idempotency_service_stores_response_hash():
    async with SessionLocal() as db:
        user_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        user = user_result.scalar_one_or_none()
        if user is None:
            pytest.skip("Seed user not in database")

        key = f"svc-{uuid.uuid4()}"
        path = f"/api/v1/billing/orders/{uuid.uuid4()}/pay"
        req_hash = hash_request("POST", path)
        body = {"payment_id": "mock_test", "status": "pending", "amount_minor": 1000, "idempotency_key": key}
        record = await idempotency_service.store(
            db,
            user_id=user.id,
            key=key,
            method="POST",
            path=path,
            request_hash=req_hash,
            response_status=200,
            response_body=body,
        )
        await db.commit()

        assert record.response_body_hash
        replay = await idempotency_service.lookup(db, user_id=user.id, key=key)
        assert replay is not None
        assert replay.response_body == body


@pytest.mark.asyncio
async def test_pay_idempotency_replays_response(client):
    buyer_email = f"buyer-{uuid.uuid4().hex[:8]}@example.com"
    seller_email = f"seller-{uuid.uuid4().hex[:8]}@example.com"
    order_id: uuid.UUID

    async with SessionLocal() as db:
        buyer = User(id=uuid.uuid4(), email=buyer_email, display_name="Buyer")
        seller = User(id=uuid.uuid4(), email=seller_email, display_name="Seller")
        db.add(buyer)
        db.add(seller)
        await db.flush()
        profile = KworkProfile(user_id=seller.id, title="Idem Shop")
        db.add(profile)
        await db.flush()
        kwork = Kwork(
            profile_id=profile.id,
            title="Mastering",
            description="Track mastering",
            price_minor=80_000,
            category="mastering",
            status="PUBLISHED",
        )
        db.add(kwork)
        await db.flush()
        order = MarketOrder(
            kwork_id=kwork.id,
            buyer_id=buyer.id,
            seller_id=seller.id,
            amount_minor=kwork.price_minor,
            status="AWAITING_PAYMENT",
        )
        db.add(order)
        await db.flush()
        order_id = order.id
        await db.commit()

    buyer_headers = await _auth_headers(client, buyer_email)
    idem = f"pay-{uuid.uuid4()}"

    first = await client.post(
        f"/api/v1/billing/orders/{order_id}/pay",
        headers={**buyer_headers, "Idempotency-Key": idem},
    )
    second = await client.post(
        f"/api/v1/billing/orders/{order_id}/pay",
        headers={**buyer_headers, "Idempotency-Key": idem},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["payment_id"] == second.json()["payment_id"]

    async with SessionLocal() as db:
        buyer_result = await db.execute(select(User).where(User.email == buyer_email))
        buyer = buyer_result.scalar_one()
        result = await db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.user_id == buyer.id,
                IdempotencyKey.key == idem,
            )
        )
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.response_body_hash
        assert record.response_body is not None
