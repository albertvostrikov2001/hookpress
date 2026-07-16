"""Inbound webhooks with HMAC verification."""

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.office_service import office_service
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppError
from app.infrastructure.security.webhook_hmac import verify_hmac_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _verify_distribution_hmac(request: Request, signature: str | None) -> bytes:
    body = await request.body()
    if not verify_hmac_signature(settings.distribution_webhook_secret, body, signature or ""):
        raise AppError("invalid_signature", "Invalid webhook signature", status_code=401)
    return body


@router.post("/distribution")
async def distribution_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_signature: Annotated[str | None, Header(alias="X-Signature")] = None,
):
    body = await _verify_distribution_hmac(request, x_signature)
    payload = json.loads(body)

    release_id = uuid.UUID(payload["release_id"])
    status = payload.get("status", "RELEASED")
    external_id = payload.get("external_id")
    job = await office_service.process_distribution_webhook(
        db,
        release_id=release_id,
        status=status,
        external_id=external_id,
        payload=payload,
    )
    return {
        "job_id": str(job.id),
        "release_id": str(release_id),
        "status": job.status,
    }
