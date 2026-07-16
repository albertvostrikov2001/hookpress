"""Market use cases."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.audit import write_audit
from app.application.media_service import media_service
from app.application.notification_service import notification_service
from app.core.errors import AppError
from app.domain.market.enums import KWORK_CATEGORIES
from app.domain.market.states import market_order_state_machine
from app.infrastructure.models.kwork import Kwork
from app.infrastructure.models.kwork_profile import KworkProfile
from app.infrastructure.models.market_order import MarketOrder
from app.infrastructure.models.order_deliverable import OrderDeliverable
from app.infrastructure.models.order_message import OrderMessage
from app.infrastructure.models.order_spec_version import OrderSpecVersion


class MarketService:
    async def get_or_create_profile(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        title: str,
        bio: str | None = None,
        skills: list[str] | None = None,
    ) -> KworkProfile:
        result = await db.execute(select(KworkProfile).where(KworkProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile:
            profile.title = title
            profile.bio = bio
            profile.skills = skills
            await db.flush()
            return profile
        profile = KworkProfile(user_id=user_id, title=title, bio=bio, skills=skills)
        db.add(profile)
        await db.flush()
        return profile

    async def get_profile(self, db: AsyncSession, profile_id: uuid.UUID) -> KworkProfile:
        result = await db.execute(
            select(KworkProfile).options(selectinload(KworkProfile.kworks)).where(KworkProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise AppError("profile_not_found", "Kwork profile not found", status_code=404)
        return profile

    async def get_profile_by_user(self, db: AsyncSession, user_id: uuid.UUID) -> KworkProfile:
        result = await db.execute(
            select(KworkProfile).options(selectinload(KworkProfile.kworks)).where(KworkProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise AppError("profile_not_found", "Kwork profile not found", status_code=404)
        return profile

    def profile_detail(self, profile: KworkProfile) -> dict:
        published = [k for k in profile.kworks if k.status == "PUBLISHED"]
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "title": profile.title,
            "bio": profile.bio,
            "skills": profile.skills,
            "is_active": profile.is_active,
            "created_at": profile.created_at,
            "kworks": published,
        }

    async def create_kwork(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        title: str,
        description: str,
        price_minor: int,
        category: str,
        tags: list[str] | None = None,
    ) -> Kwork:
        if price_minor <= 0:
            raise AppError("invalid_price", "Price must be positive (minor units)", status_code=400)
        if category not in KWORK_CATEGORIES:
            raise AppError(
                "invalid_category",
                f"Category must be one of: {', '.join(sorted(KWORK_CATEGORIES))}",
                status_code=400,
            )
        profile = await self.get_or_create_profile(db, user_id=user_id, title=f"Seller {user_id}")
        kwork = Kwork(
            profile_id=profile.id,
            title=title,
            description=description,
            price_minor=price_minor,
            category=category,
            tags=tags,
            status="DRAFT",
        )
        db.add(kwork)
        await db.flush()
        return kwork

    async def publish_kwork(self, db: AsyncSession, user_id: uuid.UUID, kwork_id: uuid.UUID) -> Kwork:
        kwork = await self._get_owned_kwork(db, user_id, kwork_id)
        kwork.status = "PUBLISHED"
        await db.flush()
        return kwork

    async def set_kwork_cover(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        kwork_id: uuid.UUID,
        cover_asset_id: uuid.UUID,
    ) -> Kwork:
        kwork = await self._get_owned_kwork(db, user_id, kwork_id)
        await media_service.get_asset(
            db, user_id=user_id, asset_id=cover_asset_id, require_ready=True
        )
        kwork.cover_asset_id = cover_asset_id
        await db.flush()
        return kwork

    async def get_kwork_preview_url(
        self,
        db: AsyncSession,
        *,
        kwork_id: uuid.UUID,
    ) -> tuple[str, int]:
        kwork = await self.get_kwork(db, kwork_id)
        if kwork.status != "PUBLISHED":
            raise AppError("kwork_not_published", "Kwork is not published", status_code=404)
        if kwork.cover_asset_id is None:
            raise AppError("no_preview", "Kwork has no cover preview", status_code=404)
        return await media_service.get_public_presigned_url(db, asset_id=kwork.cover_asset_id)

    async def add_portfolio_asset(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        kwork_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Kwork:
        kwork = await self._get_owned_kwork(db, user_id, kwork_id)
        await media_service.get_asset(
            db, user_id=user_id, asset_id=asset_id, require_ready=True
        )
        raw_ids = list(kwork.portfolio_asset_ids or [])
        asset_key = str(asset_id)
        if asset_key not in raw_ids:
            if len(raw_ids) >= 6:
                raise AppError("portfolio_full", "Portfolio supports up to 6 assets", status_code=400)
            raw_ids.append(asset_key)
        kwork.portfolio_asset_ids = raw_ids
        await db.flush()
        return kwork

    async def list_portfolio_urls(
        self,
        db: AsyncSession,
        *,
        kwork_id: uuid.UUID,
    ) -> list[dict]:
        kwork = await self.get_kwork(db, kwork_id)
        if kwork.status != "PUBLISHED":
            raise AppError("kwork_not_published", "Kwork is not published", status_code=404)
        items: list[dict] = []
        for raw in kwork.portfolio_asset_ids or []:
            asset_id = uuid.UUID(str(raw))
            url, expires_in = await media_service.get_public_presigned_url(db, asset_id=asset_id)
            items.append({"asset_id": str(asset_id), "url": url, "expires_in": expires_in})
        return items

    async def search_kworks(
        self,
        db: AsyncSession,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Kwork]:
        stmt = (
            select(Kwork)
            .join(KworkProfile)
            .where(Kwork.status == "PUBLISHED", KworkProfile.is_active.is_(True))
            .order_by(Kwork.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if category:
            stmt = stmt.where(Kwork.category == category)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(Kwork.title.ilike(pattern), Kwork.description.ilike(pattern)))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_kwork(self, db: AsyncSession, kwork_id: uuid.UUID) -> Kwork:
        result = await db.execute(
            select(Kwork).join(KworkProfile).where(Kwork.id == kwork_id, KworkProfile.is_active.is_(True))
        )
        kwork = result.scalar_one_or_none()
        if kwork is None:
            raise AppError("kwork_not_found", "Kwork not found", status_code=404)
        return kwork

    async def list_user_orders(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        limit: int = 30,
    ) -> list[MarketOrder]:
        result = await db.execute(
            select(MarketOrder)
            .where(or_(MarketOrder.buyer_id == user_id, MarketOrder.seller_id == user_id))
            .order_by(MarketOrder.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_order(
        self,
        db: AsyncSession,
        *,
        buyer_id: uuid.UUID,
        kwork_id: uuid.UUID,
    ) -> MarketOrder:
        result = await db.execute(
            select(Kwork)
            .join(KworkProfile)
            .where(Kwork.id == kwork_id, Kwork.status == "PUBLISHED")
        )
        kwork = result.scalar_one_or_none()
        if kwork is None:
            raise AppError("kwork_not_found", "Published kwork not found", status_code=404)
        profile = await db.get(KworkProfile, kwork.profile_id)
        if profile is None or profile.user_id == buyer_id:
            raise AppError("invalid_order", "Cannot order your own kwork", status_code=400)
        order = MarketOrder(
            kwork_id=kwork.id,
            buyer_id=buyer_id,
            seller_id=profile.user_id,
            amount_minor=kwork.price_minor,
            status="CREATED",
        )
        db.add(order)
        await db.flush()
        market_order_state_machine.assert_transition("CREATED", "AWAITING_PAYMENT")
        order.status = "AWAITING_PAYMENT"
        await write_audit(
            db,
            action="market.order_created",
            resource_type="market_order",
            resource_id=str(order.id),
            actor_user_id=buyer_id,
        )
        await notification_service.create(
            db,
            user_id=profile.user_id,
            type="market.order_created",
            title="New order received",
            body=f"A buyer placed an order for {kwork.title}",
            data={"order_id": str(order.id), "kwork_id": str(kwork.id)},
        )
        await db.flush()
        return order

    async def get_order(self, db: AsyncSession, order_id: uuid.UUID) -> MarketOrder:
        result = await db.execute(
            select(MarketOrder)
            .options(selectinload(MarketOrder.messages), selectinload(MarketOrder.dispute))
            .where(MarketOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            raise AppError("order_not_found", "Order not found", status_code=404)
        return order

    async def transition_order(
        self,
        db: AsyncSession,
        order: MarketOrder,
        to_status: str,
        *,
        actor_user_id: uuid.UUID | None = None,
    ) -> MarketOrder:
        market_order_state_machine.assert_transition(order.status, to_status)
        order.status = to_status
        await write_audit(
            db,
            action="market.order_transition",
            resource_type="market_order",
            resource_id=str(order.id),
            actor_user_id=actor_user_id,
            metadata={"to_status": to_status},
        )
        await db.flush()
        return order

    async def add_order_message(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        sender_id: uuid.UUID,
        body: str,
        allow_frozen: bool = False,
    ) -> OrderMessage:
        order = await self.get_order(db, order_id)
        if order.buyer_id != sender_id and order.seller_id != sender_id:
            raise AppError("forbidden", "Not a party to this order", status_code=403)
        if order.status == "IN_DISPUTE" and not allow_frozen:
            raise AppError("messages_frozen", "Order messages are frozen during dispute", status_code=409)
        message = OrderMessage(order_id=order_id, sender_id=sender_id, body=body)
        db.add(message)
        await db.flush()
        return message

    async def list_order_messages(self, db: AsyncSession, order_id: uuid.UUID) -> list[OrderMessage]:
        result = await db.execute(
            select(OrderMessage).where(OrderMessage.order_id == order_id).order_by(OrderMessage.created_at)
        )
        return list(result.scalars().all())

    async def create_spec_version(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        created_by: uuid.UUID,
        spec_body: str,
    ) -> OrderSpecVersion:
        order = await self.get_order(db, order_id)
        if created_by not in (order.buyer_id, order.seller_id):
            raise AppError("forbidden", "Not a party to this order", status_code=403)

        result = await db.execute(
            select(func.coalesce(func.max(OrderSpecVersion.version_number), 0)).where(
                OrderSpecVersion.order_id == order_id
            )
        )
        next_version = int(result.scalar_one()) + 1
        spec = OrderSpecVersion(
            order_id=order_id,
            version_number=next_version,
            spec_body=spec_body,
            created_by=created_by,
        )
        db.add(spec)
        await write_audit(
            db,
            action="market.spec_version_created",
            resource_type="order_spec_version",
            resource_id=str(spec.id),
            actor_user_id=created_by,
            metadata={"order_id": str(order_id), "version": next_version},
        )
        await db.flush()
        return spec

    async def list_spec_versions(self, db: AsyncSession, order_id: uuid.UUID) -> list[OrderSpecVersion]:
        result = await db.execute(
            select(OrderSpecVersion)
            .where(OrderSpecVersion.order_id == order_id)
            .order_by(OrderSpecVersion.version_number)
        )
        return list(result.scalars().all())

    async def add_deliverable(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        created_by: uuid.UUID,
        description: str | None = None,
        media_asset_id: uuid.UUID | None = None,
        spec_version_id: uuid.UUID | None = None,
    ) -> OrderDeliverable:
        order = await self.get_order(db, order_id)
        if created_by != order.seller_id:
            raise AppError("forbidden", "Only seller can submit deliverables", status_code=403)
        if order.status not in ("IN_PROGRESS", "REVISION_IN_PROGRESS"):
            raise AppError("invalid_order_state", "Order is not in a deliverable state", status_code=409)
        if media_asset_id:
            await media_service.get_asset(
                db, user_id=created_by, asset_id=media_asset_id, require_ready=True
            )

        result = await db.execute(
            select(func.coalesce(func.max(OrderDeliverable.revision_number), 0)).where(
                OrderDeliverable.order_id == order_id
            )
        )
        revision_number = int(result.scalar_one()) + 1

        deliverable = OrderDeliverable(
            order_id=order_id,
            spec_version_id=spec_version_id,
            revision_number=revision_number,
            description=description,
            media_asset_id=media_asset_id,
            created_by=created_by,
        )
        db.add(deliverable)
        market_order_state_machine.assert_transition(order.status, "DELIVERED")
        order.status = "DELIVERED"
        await write_audit(
            db,
            action="market.deliverable_added",
            resource_type="order_deliverable",
            resource_id=str(deliverable.id),
            actor_user_id=created_by,
            metadata={"order_id": str(order_id), "revision": revision_number},
        )
        await db.flush()
        return deliverable

    async def request_revision(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        buyer_id: uuid.UUID,
        reason: str,
    ) -> MarketOrder:
        order = await self.get_order(db, order_id)
        if buyer_id != order.buyer_id:
            raise AppError("forbidden", "Only buyer can request revision", status_code=403)
        if order.status != "DELIVERED":
            raise AppError("invalid_order_state", "Revision only allowed after delivery", status_code=409)

        order = await self.transition_order(db, order, "REVISION_REQUESTED", actor_user_id=buyer_id)
        await self.add_order_message(
            db,
            order_id=order_id,
            sender_id=buyer_id,
            body=f"Revision requested: {reason}",
        )
        return order

    async def accept_revision(
        self,
        db: AsyncSession,
        *,
        order_id: uuid.UUID,
        seller_id: uuid.UUID,
    ) -> MarketOrder:
        order = await self.get_order(db, order_id)
        if seller_id != order.seller_id:
            raise AppError("forbidden", "Only seller can accept revision", status_code=403)
        return await self.transition_order(db, order, "REVISION_IN_PROGRESS", actor_user_id=seller_id)

    async def list_deliverables(self, db: AsyncSession, order_id: uuid.UUID) -> list[OrderDeliverable]:
        result = await db.execute(
            select(OrderDeliverable)
            .where(OrderDeliverable.order_id == order_id)
            .order_by(OrderDeliverable.revision_number)
        )
        return list(result.scalars().all())

    async def _get_owned_kwork(self, db: AsyncSession, user_id: uuid.UUID, kwork_id: uuid.UUID) -> Kwork:
        result = await db.execute(
            select(Kwork)
            .join(KworkProfile)
            .where(Kwork.id == kwork_id, KworkProfile.user_id == user_id)
        )
        kwork = result.scalar_one_or_none()
        if kwork is None:
            raise AppError("kwork_not_found", "Kwork not found", status_code=404)
        return kwork


market_service = MarketService()
