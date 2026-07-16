"""Media routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, get_current_user
from app.application.media_service import media_service
from app.core.database import get_db
from app.schemas.media import (
    CompleteUploadRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    MediaAssetResponse,
    PresignedUrlResponse,
    UploadPartResponse,
    UploadPartsResponse,
)

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/uploads/initiate", response_model=InitiateUploadResponse, status_code=201)
async def initiate_upload(
    body: InitiateUploadRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    upload = await media_service.initiate_upload(
        db,
        user_id=current.user_id,
        filename=body.filename,
        content_type=body.content_type,
        total_size=body.total_size,
        ip_address=client_ip(request),
    )
    return InitiateUploadResponse(
        upload_id=upload.id,
        object_key=upload.object_key,
        bucket=upload.bucket,
    )


@router.post("/uploads/{upload_id}/parts", response_model=UploadPartResponse)
async def upload_part(
    upload_id: uuid.UUID,
    part_number: Annotated[int, Form(ge=1)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
    file: UploadFile = File(...),
):
    body = await file.read()
    upload, etag = await media_service.upload_part(
        db,
        user_id=current.user_id,
        upload_id=upload_id,
        part_number=part_number,
        body=body,
        ip_address=client_ip(request),
    )
    return UploadPartResponse(upload_id=upload.id, part_number=part_number, etag=etag)


@router.get("/uploads/{upload_id}/parts", response_model=UploadPartsResponse)
async def list_upload_parts(
    upload_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    parts = await media_service.list_upload_parts(
        db, user_id=current.user_id, upload_id=upload_id
    )
    return UploadPartsResponse(upload_id=upload_id, parts=parts)


@router.post("/uploads/{upload_id}/complete", response_model=MediaAssetResponse)
async def complete_upload(
    upload_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
    body: CompleteUploadRequest | None = None,
):
    asset = await media_service.complete_upload(
        db,
        user_id=current.user_id,
        upload_id=upload_id,
        parts=body.parts if body else None,
        ip_address=client_ip(request),
    )
    return MediaAssetResponse.model_validate(asset)


@router.get("/assets/{asset_id}/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    asset_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    url, expires_in = await media_service.get_presigned_url(
        db, user_id=current.user_id, asset_id=asset_id
    )
    return PresignedUrlResponse(url=url, expires_in=expires_in)
