"""Media API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class InitiateUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    total_size: int = Field(gt=0)


class InitiateUploadResponse(BaseModel):
    upload_id: uuid.UUID
    object_key: str
    bucket: str


class UploadPartResponse(BaseModel):
    upload_id: uuid.UUID
    part_number: int
    etag: str


class CompleteUploadRequest(BaseModel):
    parts: list[dict] = Field(min_length=1)


class MediaAssetResponse(BaseModel):
    id: uuid.UUID
    bucket: str
    object_key: str
    content_type: str
    size_bytes: int
    status: str = "UPLOADING"
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadPartsResponse(BaseModel):
    upload_id: uuid.UUID
    parts: list[dict]


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int
