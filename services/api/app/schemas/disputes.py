"""Dispute schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DisputeCreate(BaseModel):
    reason: str


class DisputeResolve(BaseModel):
    resolution: str
    refund_amount_minor: int | None = Field(default=None, ge=0)


class DisputeEvidenceCreate(BaseModel):
    body: str | None = None
    media_asset_id: uuid.UUID | None = None


class DisputeEvidenceResponse(BaseModel):
    id: uuid.UUID
    dispute_id: uuid.UUID
    uploaded_by: uuid.UUID
    body: str | None
    media_asset_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    opened_by: uuid.UUID
    status: str
    reason: str
    resolution: str | None
    refund_amount_minor: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
