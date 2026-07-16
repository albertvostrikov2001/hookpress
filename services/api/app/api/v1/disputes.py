"""Dispute routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.application.dispute_service import dispute_service
from app.application.market_service import market_service
from app.core.database import get_db
from app.domain.auth.roles import Role
from app.schemas.disputes import (
    DisputeCreate,
    DisputeEvidenceCreate,
    DisputeEvidenceResponse,
    DisputeResolve,
    DisputeResponse,
)
from app.schemas.market import MarketOrderResponse

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("/orders/{order_id}", response_model=DisputeResponse)
async def open_dispute(
    order_id: uuid.UUID,
    body: DisputeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    dispute = await dispute_service.open_dispute(
        db, order_id=order_id, opened_by=current.user_id, reason=body.reason
    )
    await db.commit()
    return dispute


@router.get("/by-order/{order_id}", response_model=DisputeResponse)
async def get_dispute_by_order(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    dispute = await dispute_service.get_dispute_by_order(db, order_id)
    order = await market_service.get_order(db, order_id)
    if current.user_id not in (order.buyer_id, order.seller_id):
        from app.core.errors import AppError

        raise AppError("forbidden", "Not a party to this order", status_code=403)
    return dispute


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    return await dispute_service.get_dispute(db, dispute_id)


@router.post("/{dispute_id}/evidence", response_model=DisputeEvidenceResponse, status_code=201)
async def add_evidence(
    dispute_id: uuid.UUID,
    body: DisputeEvidenceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    evidence = await dispute_service.add_evidence(
        db,
        dispute_id=dispute_id,
        uploaded_by=current.user_id,
        body=body.body,
        media_asset_id=body.media_asset_id,
    )
    await db.commit()
    return evidence


@router.get("/{dispute_id}/evidence", response_model=list[DisputeEvidenceResponse])
async def list_evidence(
    dispute_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    return await dispute_service.list_evidence(db, dispute_id)


@router.post("/{dispute_id}/review", response_model=DisputeResponse)
async def review_dispute(
    dispute_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(require_roles(Role.MODERATOR, Role.ADMIN)),
):
    dispute = await dispute_service.get_dispute(db, dispute_id)
    dispute = await dispute_service.transition_dispute(
        db, dispute, "UNDER_REVIEW", actor_user_id=current.user_id
    )
    await db.commit()
    return dispute


@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: uuid.UUID,
    body: DisputeResolve,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(require_roles(Role.MODERATOR, Role.ADMIN)),
):
    dispute, order = await dispute_service.resolve_dispute(
        db,
        dispute_id=dispute_id,
        resolution=body.resolution,
        refund_amount_minor=body.refund_amount_minor,
        actor_user_id=current.user_id,
    )
    await db.commit()
    return {
        "dispute": DisputeResponse.model_validate(dispute),
        "order": MarketOrderResponse.model_validate(order),
    }
