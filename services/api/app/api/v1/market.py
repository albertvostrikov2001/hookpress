"""Market routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, require_scopes
from app.application.market_service import market_service
from app.core.database import get_db
from app.domain.auth.scopes import Scope
from app.schemas.market import (
    KworkPortfolioAssetAdd,
    KworkCoverUpdate,
    KworkCreate,
    KworkProfileCreate,
    KworkProfileDetailResponse,
    KworkProfileResponse,
    KworkResponse,
    MarketOrderCreate,
    MarketOrderResponse,
    OrderDeliverableCreate,
    OrderDeliverableResponse,
    OrderMessageCreate,
    OrderMessageResponse,
    OrderSpecVersionCreate,
    OrderSpecVersionResponse,
    OrderTransitionRequest,
    RevisionRequest,
)

router = APIRouter(prefix="/market", tags=["market"])

MarketRead = Annotated[CurrentUser, Depends(require_scopes(Scope.MARKET_READ))]
MarketWrite = Annotated[CurrentUser, Depends(require_scopes(Scope.MARKET_WRITE))]


@router.post("/profiles", response_model=KworkProfileResponse)
async def upsert_profile(
    body: KworkProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    profile = await market_service.get_or_create_profile(
        db,
        user_id=current.user_id,
        title=body.title,
        bio=body.bio,
        skills=body.skills,
    )
    await db.commit()
    return profile


@router.get("/profiles/{profile_id}", response_model=KworkProfileDetailResponse)
async def get_profile(
    profile_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    profile = await market_service.get_profile(db, profile_id)
    return KworkProfileDetailResponse.model_validate(market_service.profile_detail(profile))


@router.get("/profiles/by-user/{user_id}", response_model=KworkProfileDetailResponse)
async def get_profile_by_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    profile = await market_service.get_profile_by_user(db, user_id)
    return KworkProfileDetailResponse.model_validate(market_service.profile_detail(profile))


@router.post("/kworks", response_model=KworkResponse)
async def create_kwork(
    body: KworkCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    kwork = await market_service.create_kwork(
        db,
        user_id=current.user_id,
        title=body.title,
        description=body.description,
        price_minor=body.price_minor,
        category=body.category,
        tags=body.tags,
    )
    await db.commit()
    return kwork


@router.post("/kworks/{kwork_id}/publish", response_model=KworkResponse)
async def publish_kwork(
    kwork_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    kwork = await market_service.publish_kwork(db, current.user_id, kwork_id)
    await db.commit()
    return kwork


@router.get("/kworks", response_model=list[KworkResponse])
async def search_kworks(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await market_service.search_kworks(db, query=q, category=category, limit=limit, offset=offset)


@router.get("/kworks/{kwork_id}", response_model=KworkResponse)
async def get_kwork(
    kwork_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await market_service.get_kwork(db, kwork_id)


@router.get("/kworks/{kwork_id}/preview-url")
async def get_kwork_preview_url(
    kwork_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    url, expires_in = await market_service.get_kwork_preview_url(db, kwork_id=kwork_id)
    return {"url": url, "expires_in": expires_in}


@router.patch("/kworks/{kwork_id}/cover", response_model=KworkResponse)
async def set_kwork_cover(
    kwork_id: uuid.UUID,
    body: KworkCoverUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    kwork = await market_service.set_kwork_cover(
        db,
        user_id=current.user_id,
        kwork_id=kwork_id,
        cover_asset_id=body.cover_asset_id,
    )
    await db.commit()
    return kwork


@router.post("/kworks/{kwork_id}/portfolio-assets", response_model=KworkResponse)
async def add_portfolio_asset(
    kwork_id: uuid.UUID,
    body: KworkPortfolioAssetAdd,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    kwork = await market_service.add_portfolio_asset(
        db,
        user_id=current.user_id,
        kwork_id=kwork_id,
        asset_id=body.asset_id,
    )
    await db.commit()
    return kwork


@router.get("/kworks/{kwork_id}/portfolio-urls")
async def list_portfolio_urls(
    kwork_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    items = await market_service.list_portfolio_urls(db, kwork_id=kwork_id)
    return {"items": items}


@router.get("/orders/mine", response_model=list[MarketOrderResponse])
async def list_my_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketRead,
    limit: int = Query(default=30, le=100),
):
    return await market_service.list_user_orders(db, user_id=current.user_id, limit=limit)


@router.post("/orders", response_model=MarketOrderResponse)
async def create_order(
    body: MarketOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    order = await market_service.create_order(db, buyer_id=current.user_id, kwork_id=body.kwork_id)
    await db.commit()
    return order


@router.get("/orders/{order_id}", response_model=MarketOrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketRead,
):
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    return order


@router.post("/orders/{order_id}/transition", response_model=MarketOrderResponse)
async def transition_order(
    order_id: uuid.UUID,
    body: OrderTransitionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    order = await market_service.transition_order(
        db, order, body.to_status, actor_user_id=current.user_id
    )
    await db.commit()
    return order


@router.get("/orders/{order_id}/messages", response_model=list[OrderMessageResponse])
async def list_messages(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketRead,
):
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    return await market_service.list_order_messages(db, order_id)


@router.post("/orders/{order_id}/messages", response_model=OrderMessageResponse)
async def post_message(
    order_id: uuid.UUID,
    body: OrderMessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    message = await market_service.add_order_message(
        db, order_id=order_id, sender_id=current.user_id, body=body.body
    )
    await db.commit()
    return message


@router.post("/orders/{order_id}/spec-versions", response_model=OrderSpecVersionResponse, status_code=201)
async def create_spec_version(
    order_id: uuid.UUID,
    body: OrderSpecVersionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    spec = await market_service.create_spec_version(
        db, order_id=order_id, created_by=current.user_id, spec_body=body.spec_body
    )
    await db.commit()
    return spec


@router.get("/orders/{order_id}/spec-versions", response_model=list[OrderSpecVersionResponse])
async def list_spec_versions(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketRead,
):
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    return await market_service.list_spec_versions(db, order_id)


@router.post("/orders/{order_id}/deliverables", response_model=OrderDeliverableResponse, status_code=201)
async def add_deliverable(
    order_id: uuid.UUID,
    body: OrderDeliverableCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    deliverable = await market_service.add_deliverable(
        db,
        order_id=order_id,
        created_by=current.user_id,
        description=body.description,
        media_asset_id=body.media_asset_id,
        spec_version_id=body.spec_version_id,
    )
    await db.commit()
    return deliverable


@router.get("/orders/{order_id}/deliverables", response_model=list[OrderDeliverableResponse])
async def list_deliverables(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketRead,
):
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    return await market_service.list_deliverables(db, order_id)


@router.post("/orders/{order_id}/revision-request", response_model=MarketOrderResponse)
async def request_revision(
    order_id: uuid.UUID,
    body: RevisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    order = await market_service.request_revision(
        db, order_id=order_id, buyer_id=current.user_id, reason=body.reason
    )
    await db.commit()
    return order


@router.post("/orders/{order_id}/revision-accept", response_model=MarketOrderResponse)
async def accept_revision(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: MarketWrite,
):
    order = await market_service.accept_revision(
        db, order_id=order_id, seller_id=current.user_id
    )
    await db.commit()
    return order
