"""Media upload and access use cases."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import write_audit
from app.core.config import settings
from app.core.errors import AppError
from app.domain.office.enums import MediaAssetStatus, MediaUploadStatus
from app.infrastructure.models.media_asset import MediaAsset
from app.infrastructure.models.media_asset_version import MediaAssetVersion
from app.infrastructure.models.media_upload import MediaUpload
from app.infrastructure.providers.antivirus import AntivirusScanner, MockAntivirusScanner
from app.infrastructure.storage.s3 import s3_storage


class MediaService:
    def __init__(self, scanner: AntivirusScanner | None = None) -> None:
        self._scanner = scanner or MockAntivirusScanner()

    async def initiate_upload(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
        total_size: int,
        ip_address: str | None,
    ) -> MediaUpload:
        bucket = settings.s3_bucket_media
        object_key = s3_storage.build_object_key(user_id, filename)
        upload_id = await s3_storage.create_multipart_upload(
            bucket=bucket,
            key=object_key,
            content_type=content_type,
        )
        upload = MediaUpload(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            status=MediaUploadStatus.INITIATED,
            s3_upload_id=upload_id,
            object_key=object_key,
            bucket=bucket,
            total_size=total_size,
            parts_json=[],
        )
        db.add(upload)
        await db.flush()
        await write_audit(
            db,
            action="media.upload.initiate",
            resource_type="media_upload",
            resource_id=str(upload.id),
            actor_user_id=user_id,
            ip_address=ip_address,
        )
        await db.commit()
        await db.refresh(upload)
        return upload

    async def get_upload(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
    ) -> MediaUpload:
        result = await db.execute(
            select(MediaUpload).where(MediaUpload.id == upload_id, MediaUpload.user_id == user_id)
        )
        upload = result.scalar_one_or_none()
        if upload is None:
            raise AppError("media_upload_not_found", "Upload not found", status_code=404)
        return upload

    async def list_upload_parts(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
    ) -> list[dict]:
        upload = await self.get_upload(db, user_id=user_id, upload_id=upload_id)
        return list(upload.parts_json or [])

    async def upload_part(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        part_number: int,
        body: bytes,
        ip_address: str | None,
    ) -> tuple[MediaUpload, str]:
        if part_number < 1:
            raise AppError("invalid_part_number", "Part number must be >= 1", status_code=400)

        upload = await self.get_upload(db, user_id=user_id, upload_id=upload_id)
        if upload.status == MediaUploadStatus.COMPLETED:
            raise AppError("upload_completed", "Upload already completed", status_code=409)
        if upload.s3_upload_id is None:
            raise AppError("upload_invalid", "Upload missing S3 upload id", status_code=500)

        etag = await s3_storage.upload_part(
            bucket=upload.bucket,
            key=upload.object_key,
            upload_id=upload.s3_upload_id,
            part_number=part_number,
            body=body,
        )
        parts = list(upload.parts_json or [])
        parts = [p for p in parts if p.get("PartNumber") != part_number]
        parts.append({"PartNumber": part_number, "ETag": etag})
        parts.sort(key=lambda p: p["PartNumber"])
        upload.parts_json = parts
        upload.status = MediaUploadStatus.IN_PROGRESS
        await write_audit(
            db,
            action="media.upload.part",
            resource_type="media_upload",
            resource_id=str(upload.id),
            actor_user_id=user_id,
            ip_address=ip_address,
            metadata={"part_number": part_number},
        )
        await db.commit()
        await db.refresh(upload)
        return upload, etag

    async def complete_upload(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        parts: list[dict] | None,
        ip_address: str | None,
    ) -> MediaAsset:
        upload = await self.get_upload(db, user_id=user_id, upload_id=upload_id)
        if upload.status == MediaUploadStatus.COMPLETED and upload.media_asset_id:
            result = await db.execute(select(MediaAsset).where(MediaAsset.id == upload.media_asset_id))
            asset = result.scalar_one()
            return asset

        final_parts = parts or upload.parts_json or []
        if not final_parts:
            raise AppError("no_parts", "No upload parts recorded", status_code=400)
        if upload.s3_upload_id is None:
            raise AppError("upload_invalid", "Upload missing S3 upload id", status_code=500)

        await s3_storage.complete_multipart_upload(
            bucket=upload.bucket,
            key=upload.object_key,
            upload_id=upload.s3_upload_id,
            parts=final_parts,
        )
        head = await s3_storage.head_object(bucket=upload.bucket, key=upload.object_key)
        size_bytes = head.get("ContentLength", upload.total_size or 0)

        asset = MediaAsset(
            user_id=user_id,
            bucket=upload.bucket,
            object_key=upload.object_key,
            content_type=upload.content_type,
            size_bytes=size_bytes,
            status=MediaAssetStatus.SCANNING,
        )
        db.add(asset)
        await db.flush()

        version = MediaAssetVersion(
            media_asset_id=asset.id,
            version_number=1,
            bucket=asset.bucket,
            object_key=asset.object_key,
            content_type=asset.content_type,
            size_bytes=asset.size_bytes,
        )
        db.add(version)

        upload.status = MediaUploadStatus.COMPLETED
        upload.media_asset_id = asset.id
        upload.completed_at = datetime.now(UTC)
        upload.parts_json = final_parts

        await write_audit(
            db,
            action="media.upload.complete",
            resource_type="media_asset",
            resource_id=str(asset.id),
            actor_user_id=user_id,
            ip_address=ip_address,
        )
        await db.flush()

        asset = await self._run_scan(db, asset)
        await db.commit()
        await db.refresh(asset)
        return asset

    async def _run_scan(self, db: AsyncSession, asset: MediaAsset) -> MediaAsset:
        asset.status = MediaAssetStatus.SCANNING
        await db.flush()

        result = await self._scanner.scan(bucket=asset.bucket, object_key=asset.object_key)
        if result.clean:
            asset.status = MediaAssetStatus.READY
            await write_audit(
                db,
                action="media.scan.passed",
                resource_type="media_asset",
                resource_id=str(asset.id),
                metadata={"provider": result.provider},
            )
        else:
            asset.status = MediaAssetStatus.REJECTED
            await write_audit(
                db,
                action="media.scan.rejected",
                resource_type="media_asset",
                resource_id=str(asset.id),
                metadata={"provider": result.provider, "threat": result.threat_name},
            )
        await db.flush()
        return asset

    async def get_asset(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        require_ready: bool = False,
    ) -> MediaAsset:
        result = await db.execute(
            select(MediaAsset).where(MediaAsset.id == asset_id, MediaAsset.user_id == user_id)
        )
        asset = result.scalar_one_or_none()
        if asset is None:
            raise AppError("media_asset_not_found", "Media asset not found", status_code=404)
        if require_ready and asset.status != MediaAssetStatus.READY:
            raise AppError("media_asset_not_ready", f"Media asset status is {asset.status}", status_code=409)
        return asset

    async def get_presigned_url(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> tuple[str, int]:
        asset = await self.get_asset(db, user_id=user_id, asset_id=asset_id, require_ready=True)
        expires_in = settings.presigned_url_ttl_seconds
        url = await s3_storage.generate_presigned_url(
            bucket=asset.bucket,
            key=asset.object_key,
            expires_in=expires_in,
        )
        return url, expires_in

    async def get_public_presigned_url(
        self,
        db: AsyncSession,
        *,
        asset_id: uuid.UUID,
    ) -> tuple[str, int]:
        result = await db.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        asset = result.scalar_one_or_none()
        if asset is None:
            raise AppError("media_asset_not_found", "Media asset not found", status_code=404)
        if asset.status != MediaAssetStatus.READY:
            raise AppError("media_asset_not_ready", f"Media asset status is {asset.status}", status_code=409)
        expires_in = settings.presigned_url_ttl_seconds
        url = await s3_storage.generate_presigned_url(
            bucket=asset.bucket,
            key=asset.object_key,
            expires_in=expires_in,
        )
        return url, expires_in

    async def cleanup_stale_uploads(self, db: AsyncSession, *, stale_hours: int) -> int:
        cutoff = datetime.now(UTC).replace(microsecond=0) - timedelta(hours=stale_hours)
        result = await db.execute(
            select(MediaUpload).where(
                MediaUpload.status.in_([MediaUploadStatus.INITIATED, MediaUploadStatus.IN_PROGRESS]),
                MediaUpload.created_at < cutoff,
            )
        )
        uploads = list(result.scalars().all())
        for upload in uploads:
            if upload.s3_upload_id:
                try:
                    await s3_storage.abort_multipart_upload(
                        bucket=upload.bucket,
                        key=upload.object_key,
                        upload_id=upload.s3_upload_id,
                    )
                except Exception:
                    pass
            upload.status = MediaUploadStatus.ABORTED
        if uploads:
            await db.commit()
        return len(uploads)


media_service = MediaService()
