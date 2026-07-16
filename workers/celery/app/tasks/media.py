"""Media maintenance Celery tasks."""

import asyncio
import os

from app.celery_app import celery_app


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="media.cleanup_stale_uploads")
def cleanup_stale_uploads():
    stale_hours = int(os.getenv("MEDIA_UPLOAD_STALE_HOURS", "24"))

    async def _cleanup():
        from app.application.media_service import media_service
        from app.core.database import SessionLocal

        async with SessionLocal() as db:
            return await media_service.cleanup_stale_uploads(db, stale_hours=stale_hours)

    count = _run_async(_cleanup())
    return {"aborted": count}
