"""Billing schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    account_id: uuid.UUID
    balance_minor: int
    currency: str = "RUB"


class PaymentInitiateResponse(BaseModel):
    payment_id: str
    status: str
    amount_minor: int
    idempotency_key: str


class PaymentWebhookPayload(BaseModel):
    order_id: uuid.UUID
    amount_minor: int = Field(gt=0)


class ReconciliationResponse(BaseModel):
    system_balance_minor: int
    commission_balance_minor: int
    escrow_total_minor: int
    wallet_total_minor: int
    escrow_account_count: int
    wallet_account_count: int
    balanced: bool
    platform_commission_bps: int


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    amount_minor: int
    entry_type: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}
