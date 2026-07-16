"""S3 helpers for Celery workers."""

import uuid

import boto3
from botocore.client import Config
from sqlalchemy.orm import Session

from app.config import settings
from app.db import MediaAsset


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4"),
    )


def upload_bytes(*, user_id: uuid.UUID, data: bytes, content_type: str, suffix: str) -> MediaAsset:
    asset_id = uuid.uuid4()
    object_key = f"studio/{user_id}/{asset_id}{suffix}"
    client = _s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_media,
        Key=object_key,
        Body=data,
        ContentType=content_type,
    )
    return MediaAsset(
        id=asset_id,
        user_id=user_id,
        bucket=settings.s3_bucket_media,
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(data),
    )


def download_object_to_file(asset_id: uuid.UUID, dest_path: str, *, session: Session) -> str:
    asset = session.get(MediaAsset, asset_id)
    if asset is None:
        raise FileNotFoundError(f"media asset {asset_id} not found")
    client = _s3_client()
    client.download_file(asset.bucket, asset.object_key, dest_path)
    return dest_path
