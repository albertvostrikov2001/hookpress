"""Release ORM model."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

release_status_enum = ENUM(
    "DRAFT",
    "VALIDATING",
    "MODERATION",
    "DELIVERED",
    "RELEASED",
    "REJECTED",
    "FAILED",
    name="release_status",
    create_type=False,
)

release_type_enum = ENUM(
    "SINGLE",
    "EP",
    "ALBUM",
    name="release_type",
    create_type=False,
)


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    office_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("office_projects.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(release_status_enum, default="DRAFT", index=True)
    release_type: Mapped[str] = mapped_column(release_type_enum, default="SINGLE")
    contributors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cover_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_test_code: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    office_project: Mapped["OfficeProject"] = relationship(back_populates="releases")
    distribution_jobs: Mapped[list["DistributionJob"]] = relationship(back_populates="release", lazy="selectin")
    scoring_reports: Mapped[list["ScoringReport"]] = relationship(back_populates="release", lazy="selectin")
