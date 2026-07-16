"""Media asset ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

media_asset_status_enum = ENUM(
    "UPLOADING",
    "SCANNING",
    "READY",
    "REJECTED",
    name="media_asset_status",
    create_type=False,
)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (UniqueConstraint("bucket", "object_key", name="uq_media_assets_bucket_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    bucket: Mapped[str] = mapped_column(String(128))
    object_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(media_asset_status_enum, default="UPLOADING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    versions: Mapped[list["MediaAssetVersion"]] = relationship(back_populates="media_asset", lazy="selectin")
