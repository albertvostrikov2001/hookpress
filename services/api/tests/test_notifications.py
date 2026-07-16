"""Notification domain tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.application.market_service import market_service
from app.core.database import SessionLocal
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.notification import Notification
from app.infrastructure.models.user import User
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
async def test_market_order_creates_seller_notification():
    async with SessionLocal() as db:
        buyer_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        buyer = buyer_result.scalar_one_or_none()
        if buyer is None:
            pytest.skip("Seed user not in database")

        seller = User(
            id=uuid.uuid4(),
            email=f"seller-{uuid.uuid4().hex[:8]}@example.com",
            display_name="Notify Seller",
        )
        db.add(seller)
        await db.flush()
        profile = KworkProfile(user_id=seller.id, title="Notify Shop")
        db.add(profile)
        await db.flush()
        kwork = Kwork(
            profile_id=profile.id,
            title="Beat production",
            description="Custom beat",
            price_minor=50_000,
            category="production",
            status="PUBLISHED",
        )
        db.add(kwork)
        await db.flush()

        await market_service.create_order(db, buyer_id=buyer.id, kwork_id=kwork.id)
        await db.commit()

        result = await db.execute(
            select(Notification).where(
                Notification.user_id == seller.id,
                Notification.type == "market.order_created",
            )
        )
        notification = result.scalar_one_or_none()
        assert notification is not None
        assert "Beat production" in (notification.body or "")


@pytest.mark.asyncio
async def test_list_and_mark_notifications(client):
    headers = await _auth_headers(client)
    listed = await client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert "items" in body
    assert "unread_count" in body
    assert "has_more" in body

    if body["items"]:
        notification_id = body["items"][0]["id"]
        marked = await client.post(
            f"/api/v1/notifications/{notification_id}/read",
            headers=headers,
        )
        assert marked.status_code == 200
        assert marked.json()["read_at"] is not None

    mark_all = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert mark_all.status_code == 200
    assert "marked" in mark_all.json()
