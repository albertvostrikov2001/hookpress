"""One-time demo setup helpers (Render deploy)."""

import logging

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.errors import AppError
from app.infrastructure.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["setup"])


@router.post("/seed")
async def run_demo_seed():
    """Create demo users and content if missing (dev/demo deploys only)."""
    if not settings.dev_login_enabled:
        raise AppError("forbidden", "Demo seed is disabled", status_code=403)

    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(User))

    from scripts.seed import seed

    await seed()

    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(User))

    logger.info("Demo seed via /setup/seed — users=%s", count)
    return {"status": "ok", "users": count or 0}


@router.get("/status")
async def setup_status():
    async with SessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(User))
    return {"users": count or 0, "dev_login_enabled": settings.dev_login_enabled}
