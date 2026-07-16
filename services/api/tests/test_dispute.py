"""Dispute and message freeze tests."""

import uuid

import pytest
from sqlalchemy import select

from app.application.billing_service import billing_service
from app.application.dispute_service import dispute_service
from app.application.market_service import market_service
from app.core.database import SessionLocal
from app.core.errors import AppError
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.order_message import OrderMessage
from app.infrastructure.models.user import User
from app.infrastructure.providers.payment import MockPaymentProvider

DEV_EMAIL = "artist@example.com"


@pytest.mark.asyncio
async def test_dispute_freezes_messages_and_refunds():
    async with SessionLocal() as db:
        buyer_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        buyer = buyer_result.scalar_one_or_none()
        if buyer is None:
            pytest.skip("Seed user not in database")

        seller = User(
            id=uuid.uuid4(),
            email=f"seller-{uuid.uuid4().hex[:8]}@example.com",
            display_name="Dispute Seller",
        )
        db.add(seller)
        await db.flush()
        profile = KworkProfile(user_id=seller.id, title="Dispute Shop")
        db.add(profile)
        await db.flush()
        kwork = Kwork(
            profile_id=profile.id,
            title="Mastering",
            description="Album mastering",
            price_minor=100_000,
            category="mastering",
            status="PUBLISHED",
        )
        db.add(kwork)
        await db.flush()

        order = await market_service.create_order(db, buyer_id=buyer.id, kwork_id=kwork.id)
        provider = MockPaymentProvider()
        await billing_service.process_payment_webhook(
            db,
            provider,
            payload={"order_id": str(order.id), "amount_minor": order.amount_minor},
            idempotency_key=f"dispute-pay-{order.id}",
        )
        order = await market_service.transition_order(db, order, "IN_PROGRESS", actor_user_id=seller.id)
        await market_service.add_order_message(db, order_id=order.id, sender_id=buyer.id, body="Hello")
        await db.flush()

        dispute = await dispute_service.open_dispute(
            db, order_id=order.id, opened_by=buyer.id, reason="Quality issues"
        )
        assert dispute.status == "OPEN"
        assert order.status == "IN_DISPUTE"

        result = await db.execute(select(OrderMessage).where(OrderMessage.order_id == order.id))
        messages = list(result.scalars().all())
        assert all(m.frozen_at is not None for m in messages)

        with pytest.raises(AppError) as exc:
            await market_service.add_order_message(
                db, order_id=order.id, sender_id=buyer.id, body="Blocked"
            )
        assert exc.value.code == "messages_frozen"

        dispute, order = await dispute_service.resolve_dispute(
            db,
            dispute_id=dispute.id,
            resolution="Full refund approved",
            refund_amount_minor=order.amount_minor,
            actor_user_id=buyer.id,
        )
        await db.commit()
        assert dispute.status == "CLOSED"
        assert order.status == "REFUNDED"
