"""Office project ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

office_project_status_enum = ENUM(
    "DRAFT_IN_STUDIO",
    "DRAFT_IN_OFFICE",
    "READY_FOR_RELEASE",
    name="office_project_status",
    create_type=False,
)


class OfficeProject(Base):
    __tablename__ = "office_projects"
    __table_args__ = (
        UniqueConstraint("studio_project_id", name="uq_office_projects_studio_project"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_office_projects_idempotency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    studio_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(office_project_status_enum, default="DRAFT_IN_OFFICE")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    studio_project: Mapped["StudioProject"] = relationship(back_populates="office_project")
    tracks: Mapped[list["Track"]] = relationship(back_populates="office_project", lazy="selectin")
    releases: Mapped[list["Release"]] = relationship(back_populates="office_project", lazy="selectin")
