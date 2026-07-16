"""AI task ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

ai_task_status_enum = ENUM(
    "PENDING",
    "PROCESSING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    name="ai_task_status",
    create_type=False,
)


class AiTask(Base):
    __tablename__ = "ai_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studio_projects.id", ondelete="CASCADE"), index=True
    )
    task_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(ai_task_status_enum, default="PENDING", index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    studio_project: Mapped["StudioProject"] = relationship(back_populates="ai_tasks")
