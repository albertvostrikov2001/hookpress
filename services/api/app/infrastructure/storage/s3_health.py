"""MinIO/S3 connectivity check."""

import httpx

from app.core.config import settings


async def ping_s3() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.s3_endpoint}/minio/health/live")
            return response.status_code == 200
    except Exception:
        return False
