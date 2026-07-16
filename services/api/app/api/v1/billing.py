"""Billing routes."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, IdempotencyContext, get_current_user, require_idempotency, require_roles
from app.application.billing_service import billing_service
from app.application.idempotency_service import idempotency_service
from app.application.market_service import market_service
from app.core.database import get_db
from app.core.metrics import BILLING_WEBHOOKS
from app.core.redis import redis_client
from app.domain.auth.roles import Role
from app.infrastructure.providers.factory import get_payment_provider
from app.schemas.billing import (
    LedgerEntryResponse,
    PaymentInitiateResponse,
    PaymentWebhookPayload,
    ReconciliationResponse,
    WalletBalanceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

_processed: set[str] = set()


async def _is_duplicate(key: str) -> bool:
    try:
        if await redis_client.get(f"billing:webhook:{key}"):
            return True
    except Exception:
        logger.warning("billing idempotency redis read failed", exc_info=True)
    return key in _processed


async def _mark_processed(key: str, event_id: str) -> None:
    _processed.add(key)
    try:
        await redis_client.setex(f"billing:webhook:{key}", 86400, event_id)
    except Exception:
        logger.warning("billing idempotency redis write failed", exc_info=True)


@router.get("/wallet", response_model=WalletBalanceResponse)
async def get_wallet(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
):
    account = await billing_service.ensure_wallet(db, current.user_id)
    balance = await billing_service.get_balance(db, account.id)
    return WalletBalanceResponse(account_id=account.id, balance_minor=balance)


@router.get("/wallet/entries", response_model=list[LedgerEntryResponse])
async def list_wallet_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(default=50, le=200),
):
    entries = await billing_service.list_wallet_entries(db, user_id=current.user_id, limit=limit)
    return [LedgerEntryResponse.model_validate(e) for e in entries]


@router.post("/orders/{order_id}/pay", response_model=PaymentInitiateResponse)
async def initiate_payment(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    idem: Annotated[IdempotencyContext, Depends(require_idempotency())],
):
    if idem.replay_body is not None:
        return PaymentInitiateResponse.model_validate(idem.replay_body)

    intent = await billing_service.initiate_payment(
        db,
        get_payment_provider(),
        order_id=order_id,
        buyer_id=current.user_id,
        idempotency_key=idem.key,
    )
    await db.commit()
    response = PaymentInitiateResponse(
        payment_id=intent.payment_id,
        status=intent.status,
        amount_minor=intent.amount_minor,
        idempotency_key=idem.key,
    )
    await idempotency_service.store(
        db,
        user_id=current.user_id,
        key=idem.key,
        method=idem.method,
        path=idem.path,
        request_hash=idem.request_hash,
        response_status=200,
        response_body=response.model_dump(mode="json"),
    )
    await db.commit()
    return response


@router.post("/webhooks/payment")
async def payment_webhook(
    body: PaymentWebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
):
    if await _is_duplicate(idempotency_key):
        BILLING_WEBHOOKS.labels(result="duplicate").inc()
        order = await market_service.get_order(db, body.order_id)
        return {"order_id": str(order.id), "status": order.status, "duplicate": True}

    order = await billing_service.process_payment_webhook(
        db,
        get_payment_provider(),
        payload={"order_id": str(body.order_id), "amount_minor": body.amount_minor},
        idempotency_key=idempotency_key,
    )
    await _mark_processed(idempotency_key, str(body.order_id))
    BILLING_WEBHOOKS.labels(result="processed").inc()
    return {"order_id": str(order.id), "status": order.status, "duplicate": False}


@router.post("/orders/{order_id}/capture")
async def capture_order(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    key = idempotency_key or f"capture:{order_id}"
    order = await market_service.get_order(db, order_id)
    await billing_service.capture_funds(
        db,
        seller_id=order.seller_id,
        order_id=order_id,
        amount_minor=order.amount_minor,
        idempotency_key=key,
    )
    if order.status != "COMPLETED":
        order = await market_service.transition_order(db, order, "COMPLETED", actor_user_id=current.user_id)
    await db.commit()
    return {"order_id": str(order_id), "status": order.status}


@router.get("/reconciliation", response_model=ReconciliationResponse)
async def billing_reconciliation(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
):
    return await billing_service.reconciliation(db)
