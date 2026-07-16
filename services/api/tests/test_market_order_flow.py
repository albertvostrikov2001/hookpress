"""Market order flow tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.application.billing_service import billing_service
from app.application.market_service import market_service
from app.core.database import SessionLocal
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.user import User
from app.infrastructure.providers.payment import MockPaymentProvider
from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_market_order_state_flow():
    async with SessionLocal() as db:
        buyer_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        buyer = buyer_result.scalar_one_or_none()
        if buyer is None:
            pytest.skip("Seed user not in database")

        seller = User(
            id=uuid.uuid4(),
            email=f"seller-{uuid.uuid4().hex[:8]}@example.com",
            display_name="Test Seller",
        )
        db.add(seller)
        await db.flush()
        profile = KworkProfile(user_id=seller.id, title="Seller Shop")
        db.add(profile)
        await db.flush()
        kwork = Kwork(
            profile_id=profile.id,
            title="Beat Production",
            description="Custom beat",
            price_minor=250_000,
            category="production",
            status="PUBLISHED",
        )
        db.add(kwork)
        await db.flush()

        order = await market_service.create_order(db, buyer_id=buyer.id, kwork_id=kwork.id)
        assert order.status == "AWAITING_PAYMENT"

        provider = MockPaymentProvider()
        idem = f"flow-{uuid.uuid4()}"
        await billing_service.process_payment_webhook(
            db,
            provider,
            payload={"order_id": str(order.id), "amount_minor": order.amount_minor},
            idempotency_key=idem,
        )
        order = await market_service.get_order(db, order.id)
        assert order.status == "FUNDS_HELD"

        order = await market_service.transition_order(db, order, "IN_PROGRESS", actor_user_id=seller.id)
        order = await market_service.transition_order(db, order, "DELIVERED", actor_user_id=seller.id)
        order = await market_service.transition_order(db, order, "COMPLETED", actor_user_id=buyer.id)
        await billing_service.capture_funds(
            db,
            seller_id=seller.id,
            order_id=order.id,
            amount_minor=order.amount_minor,
            idempotency_key=f"capture-{order.id}",
        )
        await db.commit()
        assert order.status == "COMPLETED"


@pytest.mark.asyncio
async def test_search_published_kworks(client):
    headers = {}
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}

    created = await client.post(
        "/api/v1/market/kworks",
        headers=headers,
        json={
            "title": "Vocal Tuning",
            "description": "Pitch correction service",
            "price_minor": 80_000,
            "category": "sound_engineering",
        },
    )
    assert created.status_code == 200
    kid = created.json()["id"]
    await client.post(f"/api/v1/market/kworks/{kid}/publish", headers=headers)

    search = await client.get("/api/v1/market/kworks", params={"q": "Vocal"})
    assert search.status_code == 200
    titles = [k["title"] for k in search.json()]
    assert "Vocal Tuning" in titles
