"""S3-compatible object storage."""

import uuid

import aioboto3
from botocore.client import Config

from app.core.config import settings
from app.core.metrics import record_storage_bytes


def _client_kwargs() -> dict:
    return {
        "endpoint_url": settings.s3_endpoint,
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key,
        "use_ssl": settings.s3_use_ssl,
        "config": Config(signature_version="s3v4"),
    }


class S3Storage:
    def __init__(self) -> None:
        self._session = aioboto3.Session()

    async def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str:
        async with self._session.client("s3", **_client_kwargs()) as client:
            response = await client.create_multipart_upload(
                Bucket=bucket,
                Key=key,
                ContentType=content_type,
            )
            return response["UploadId"]

    async def upload_part(
        self,
        *,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
    ) -> str:
        async with self._session.client("s3", **_client_kwargs()) as client:
            response = await client.upload_part(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=body,
            )
            record_storage_bytes(bucket, "upload", len(body))
            return response["ETag"]

    async def complete_multipart_upload(
        self,
        *,
        bucket: str,
        key: str,
        upload_id: str,
        parts: list[dict],
    ) -> None:
        normalized = [
            {
                "PartNumber": p.get("PartNumber") or p.get("part_number"),
                "ETag": p.get("ETag") or p.get("etag"),
            }
            for p in parts
        ]
        async with self._session.client("s3", **_client_kwargs()) as client:
            await client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": normalized},
            )

    async def abort_multipart_upload(self, *, bucket: str, key: str, upload_id: str) -> None:
        async with self._session.client("s3", **_client_kwargs()) as client:
            await client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)

    async def head_object(self, *, bucket: str, key: str) -> dict:
        async with self._session.client("s3", **_client_kwargs()) as client:
            return await client.head_object(Bucket=bucket, Key=key)

    async def generate_presigned_url(self, *, bucket: str, key: str, expires_in: int) -> str:
        async with self._session.client("s3", **_client_kwargs()) as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    def build_object_key(self, user_id: uuid.UUID, filename: str) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return f"users/{user_id}/{uuid.uuid4()}/{safe_name}"


s3_storage = S3Storage()
