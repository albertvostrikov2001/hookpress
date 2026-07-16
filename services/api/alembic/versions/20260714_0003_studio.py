"""Studio tables: projects, lyric versions, AI tasks."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0003"
down_revision: Union[str, None] = "20260714_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ai_task_status = postgresql.ENUM(
    "PENDING",
    "PROCESSING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    name="ai_task_status",
    create_type=False,
)


def upgrade() -> None:
    ai_task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "studio_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_studio_projects_user_id"), "studio_projects", ["user_id"], unique=False)

    op.create_table(
        "ai_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("studio_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("status", ai_task_status, nullable=False, server_default="PENDING"),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["studio_project_id"], ["studio_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_tasks_studio_project_id"), "ai_tasks", ["studio_project_id"], unique=False)
    op.create_index(op.f("ix_ai_tasks_status"), "ai_tasks", ["status"], unique=False)

    op.create_table(
        "lyric_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("studio_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("ai_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ai_task_id"], ["ai_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["studio_project_id"], ["studio_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("studio_project_id", "version_number", name="uq_lyric_versions_project_version"),
    )
    op.create_index(
        op.f("ix_lyric_versions_studio_project_id"), "lyric_versions", ["studio_project_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_lyric_versions_studio_project_id"), table_name="lyric_versions")
    op.drop_table("lyric_versions")
    op.drop_index(op.f("ix_ai_tasks_status"), table_name="ai_tasks")
    op.drop_index(op.f("ix_ai_tasks_studio_project_id"), table_name="ai_tasks")
    op.drop_table("ai_tasks")
    op.drop_index(op.f("ix_studio_projects_user_id"), table_name="studio_projects")
    op.drop_table("studio_projects")
    ai_task_status.drop(op.get_bind(), checkfirst=True)
