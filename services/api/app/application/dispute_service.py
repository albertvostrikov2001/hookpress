"""Dispute resolution with order message freeze."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import write_audit
from app.application.billing_service import billing_service
from app.application.market_service import market_service
from app.application.media_service import media_service
from app.core.errors import AppError
from app.domain.market.states import dispute_state_machine
from app.infrastructure.models.dispute import Dispute
from app.infrastructure.models.dispute_evidence import DisputeEvidence
from app.infrastructure.models.market_order import MarketOrder
from app.infrastructure.models.order_message import OrderMessage


class DisputeService:
    async def open_dispute(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        opened_by: uuid.UUID,
        reason: str,
    ) -> Dispute:
        order = await market_service.get_order(db, order_id)
        if opened_by not in (order.buyer_id, order.seller_id):
            raise AppError("forbidden", "Not a party to this order", status_code=403)
        if order.status not in ("IN_PROGRESS", "DELIVERED"):
            raise AppError("invalid_order_state", "Order cannot enter dispute", status_code=409)
        existing = await db.execute(select(Dispute).where(Dispute.order_id == order_id))
        if existing.scalar_one_or_none():
            raise AppError("dispute_exists", "Dispute already open for this order", status_code=409)

        dispute = Dispute(order_id=order_id, opened_by=opened_by, reason=reason, status="OPEN")
        db.add(dispute)
        await market_service.transition_order(db, order, "IN_DISPUTE", actor_user_id=opened_by)
        now = datetime.now(UTC)
        await db.execute(
            update(OrderMessage)
            .where(OrderMessage.order_id == order_id, OrderMessage.frozen_at.is_(None))
            .values(frozen_at=now)
        )
        await write_audit(
            db,
            action="dispute.opened",
            resource_type="dispute",
            resource_id=str(dispute.id),
            actor_user_id=opened_by,
        )
        await db.flush()
        return dispute

    async def add_evidence(
        self,
        db: AsyncSession,
        *,
        dispute_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        body: str | None = None,
        media_asset_id: uuid.UUID | None = None,
    ) -> DisputeEvidence:
        dispute = await self.get_dispute(db, dispute_id)
        order = await market_service.get_order(db, dispute.order_id)
        if uploaded_by not in (order.buyer_id, order.seller_id):
            raise AppError("forbidden", "Not a party to this dispute", status_code=403)
        if dispute.status in ("RESOLVED", "CLOSED"):
            raise AppError("dispute_closed", "Cannot add evidence to closed dispute", status_code=409)
        if not body and not media_asset_id:
            raise AppError("evidence_empty", "Evidence requires body or attachment", status_code=400)
        if media_asset_id:
            await media_service.get_asset(
                db, user_id=uploaded_by, asset_id=media_asset_id, require_ready=True
            )

        evidence = DisputeEvidence(
            dispute_id=dispute_id,
            uploaded_by=uploaded_by,
            body=body,
            media_asset_id=media_asset_id,
        )
        db.add(evidence)
        await write_audit(
            db,
            action="dispute.evidence_added",
            resource_type="dispute_evidence",
            resource_id=str(evidence.id),
            actor_user_id=uploaded_by,
            metadata={"dispute_id": str(dispute_id)},
        )
        await db.flush()
        return evidence

    async def list_evidence(self, db: AsyncSession, dispute_id: uuid.UUID) -> list[DisputeEvidence]:
        result = await db.execute(
            select(DisputeEvidence)
            .where(DisputeEvidence.dispute_id == dispute_id)
            .order_by(DisputeEvidence.created_at)
        )
        return list(result.scalars().all())

    async def get_dispute(self, db: AsyncSession, dispute_id: uuid.UUID) -> Dispute:
        result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
        dispute = result.scalar_one_or_none()
        if dispute is None:
            raise AppError("dispute_not_found", "Dispute not found", status_code=404)
        return dispute

    async def get_dispute_by_order(self, db: AsyncSession, order_id: uuid.UUID) -> Dispute:
        result = await db.execute(select(Dispute).where(Dispute.order_id == order_id))
        dispute = result.scalar_one_or_none()
        if dispute is None:
            raise AppError("dispute_not_found", "No dispute for this order", status_code=404)
        return dispute

    async def transition_dispute(
        self,
        db: AsyncSession,
        dispute: Dispute,
        to_status: str,
        *,
        actor_user_id: uuid.UUID | None = None,
    ) -> Dispute:
        dispute_state_machine.assert_transition(dispute.status, to_status)
        dispute.status = to_status
        await write_audit(
            db,
            action="dispute.transition",
            resource_type="dispute",
            resource_id=str(dispute.id),
            actor_user_id=actor_user_id,
            metadata={"to_status": to_status},
        )
        await db.flush()
        return dispute

    async def resolve_dispute(
        self,
        db: AsyncSession,
        *,
        dispute_id: uuid.UUID,
        resolution: str,
        refund_amount_minor: int | None,
        actor_user_id: uuid.UUID,
    ) -> tuple[Dispute, MarketOrder]:
        dispute = await self.get_dispute(db, dispute_id)
        if dispute.status not in ("OPEN", "UNDER_REVIEW"):
            raise AppError("invalid_dispute_state", "Dispute cannot be resolved", status_code=409)
        order = await market_service.get_order(db, dispute.order_id)
        dispute.resolution = resolution
        dispute.refund_amount_minor = refund_amount_minor

        if dispute.status == "OPEN":
            await self.transition_dispute(db, dispute, "UNDER_REVIEW", actor_user_id=actor_user_id)

        if refund_amount_minor is None or refund_amount_minor == 0:
            await billing_service.capture_funds(
                db,
                seller_id=order.seller_id,
                order_id=order.id,
                amount_minor=order.amount_minor,
                idempotency_key=f"dispute:{dispute_id}:capture",
            )
            await market_service.transition_order(db, order, "COMPLETED", actor_user_id=actor_user_id)
            await self.transition_dispute(db, dispute, "RESOLVED", actor_user_id=actor_user_id)
        elif refund_amount_minor >= order.amount_minor:
            await billing_service.refund_funds(
                db,
                buyer_id=order.buyer_id,
                order_id=order.id,
                amount_minor=order.amount_minor,
                idempotency_key=f"dispute:{dispute_id}:refund",
            )
            await market_service.transition_order(db, order, "REFUNDED", actor_user_id=actor_user_id)
            await self.transition_dispute(db, dispute, "RESOLVED", actor_user_id=actor_user_id)
        else:
            await billing_service.refund_funds(
                db,
                buyer_id=order.buyer_id,
                order_id=order.id,
                amount_minor=refund_amount_minor,
                idempotency_key=f"dispute:{dispute_id}:partial",
                partial=True,
            )
            remainder = order.amount_minor - refund_amount_minor
            await billing_service.capture_funds(
                db,
                seller_id=order.seller_id,
                order_id=order.id,
                amount_minor=remainder,
                idempotency_key=f"dispute:{dispute_id}:capture_remainder",
            )
            await market_service.transition_order(
                db, order, "PARTIALLY_REFUNDED", actor_user_id=actor_user_id
            )
            await self.transition_dispute(db, dispute, "RESOLVED", actor_user_id=actor_user_id)

        await self.transition_dispute(db, dispute, "CLOSED", actor_user_id=actor_user_id)
        await write_audit(
            db,
            action="dispute.resolved",
            resource_type="dispute",
            resource_id=str(dispute.id),
            actor_user_id=actor_user_id,
            metadata={
                "resolution": resolution,
                "refund_amount_minor": refund_amount_minor,
                "order_id": str(order.id),
            },
        )
        await db.flush()
        return dispute, order


dispute_service = DisputeService()
