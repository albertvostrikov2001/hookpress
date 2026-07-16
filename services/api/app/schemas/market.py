"""Market schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class KworkProfileCreate(BaseModel):
    title: str = Field(max_length=200)
    bio: str | None = None
    skills: list[str] | None = None


class KworkProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    bio: str | None
    skills: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KworkProfileDetailResponse(KworkProfileResponse):
    kworks: list["KworkResponse"] = Field(default_factory=list)


class KworkCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str
    price_minor: int = Field(gt=0, description="Price in kopecks/cents")
    category: str = Field(max_length=80)
    tags: list[str] | None = None


class KworkResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    title: str
    description: str
    price_minor: int
    category: str
    tags: list[str] | None
    status: str
    cover_asset_id: uuid.UUID | None = None
    portfolio_asset_ids: list[uuid.UUID] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KworkCoverUpdate(BaseModel):
    cover_asset_id: uuid.UUID


class KworkPortfolioAssetAdd(BaseModel):
    asset_id: uuid.UUID


class MarketOrderCreate(BaseModel):
    kwork_id: uuid.UUID


class MarketOrderResponse(BaseModel):
    id: uuid.UUID
    kwork_id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    amount_minor: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderMessageCreate(BaseModel):
    body: str


class OrderMessageResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    frozen_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderTransitionRequest(BaseModel):
    to_status: str


class OrderSpecVersionCreate(BaseModel):
    spec_body: str = Field(min_length=1)


class OrderSpecVersionResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    version_number: int
    spec_body: str
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderDeliverableCreate(BaseModel):
    description: str | None = None
    media_asset_id: uuid.UUID | None = None
    spec_version_id: uuid.UUID | None = None


class OrderDeliverableResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    spec_version_id: uuid.UUID | None
    revision_number: int
    description: str | None
    media_asset_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RevisionRequest(BaseModel):
    reason: str = Field(min_length=1)


KworkProfileDetailResponse.model_rebuild()
