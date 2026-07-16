"""Studio project ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StudioProject(Base):
    __tablename__ = "studio_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    theme: Mapped[str | None] = mapped_column(String(200), nullable=True)
    mood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    structure_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lyric_versions: Mapped[list["LyricVersion"]] = relationship(back_populates="studio_project", lazy="selectin")
    ai_tasks: Mapped[list["AiTask"]] = relationship(back_populates="studio_project", lazy="selectin")
    office_project: Mapped["OfficeProject | None"] = relationship(back_populates="studio_project", uselist=False, lazy="selectin")
    assistant_messages: Mapped[list["StudioAssistantMessage"]] = relationship(
        back_populates="studio_project", lazy="selectin"
    )
