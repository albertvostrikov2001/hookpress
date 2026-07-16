"""Platform commission on capture tests."""

import uuid

import pytest
from sqlalchemy import select

from app.application.billing_service import billing_service
from app.application.market_service import market_service
from app.core.config import settings
from app.core.database import SessionLocal
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.user import User
from app.infrastructure.providers.payment import MockPaymentProvider

DEV_EMAIL = "artist@example.com"


@pytest.mark.asyncio
async def test_capture_splits_commission():
    async with SessionLocal() as db:
        buyer_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        buyer = buyer_result.scalar_one_or_none()
        if buyer is None:
            pytest.skip("Seed user not in database")

        seller = User(
            id=uuid.uuid4(),
            email=f"seller-{uuid.uuid4().hex[:8]}@example.com",
            display_name="Commission Seller",
        )
        db.add(seller)
        await db.flush()
        profile = KworkProfile(user_id=seller.id, title="Commission Shop")
        db.add(profile)
        await db.flush()
        kwork = Kwork(
            profile_id=profile.id,
            title="Mixing Service",
            description="Commission test",
            price_minor=100_000,
            category="sound_engineering",
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
            idempotency_key=f"comm-{uuid.uuid4()}",
        )
        await market_service.transition_order(db, order, "IN_PROGRESS", actor_user_id=seller.id)
        await market_service.transition_order(db, order, "DELIVERED", actor_user_id=seller.id)

        commission_account = await billing_service.ensure_commission(db)
        commission_before = await billing_service.get_balance(db, commission_account.id)
        seller_wallet = await billing_service.ensure_wallet(db, seller.id)
        seller_before = await billing_service.get_balance(db, seller_wallet.id)

        await billing_service.capture_funds(
            db,
            seller_id=seller.id,
            order_id=order.id,
            amount_minor=order.amount_minor,
            idempotency_key=f"capture-comm-{order.id}",
        )
        await db.commit()

        seller_balance = await billing_service.get_balance(db, seller_wallet.id)
        commission_balance = await billing_service.get_balance(db, commission_account.id)

        expected_commission = (order.amount_minor * settings.platform_commission_bps) // 10_000
        expected_payout = order.amount_minor - expected_commission
        assert seller_balance - seller_before == expected_payout
        assert commission_balance - commission_before == expected_commission


@pytest.mark.asyncio
async def test_reconciliation_balanced():
    async with SessionLocal() as db:
        report = await billing_service.reconciliation(db)
        assert "commission_balance_minor" in report
        assert "balanced" in report
        assert report["platform_commission_bps"] == settings.platform_commission_bps
