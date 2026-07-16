"""Studio extras: theme/mood/genre, assistant messages, task metadata."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0012"
down_revision: Union[str, None] = "20260714_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("studio_projects", sa.Column("theme", sa.String(length=200), nullable=True))
    op.add_column("studio_projects", sa.Column("mood", sa.String(length=100), nullable=True))
    op.add_column("studio_projects", sa.Column("genre", sa.String(length=100), nullable=True))
    op.add_column(
        "studio_projects",
        sa.Column("structure_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "ai_tasks",
        sa.Column("result_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "studio_assistant_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("studio_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["studio_project_id"], ["studio_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_studio_assistant_messages_studio_project_id"),
        "studio_assistant_messages",
        ["studio_project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_studio_assistant_messages_studio_project_id"),
        table_name="studio_assistant_messages",
    )
    op.drop_table("studio_assistant_messages")
    op.drop_column("ai_tasks", "result_metadata")
    op.drop_column("studio_projects", "structure_json")
    op.drop_column("studio_projects", "genre")
    op.drop_column("studio_projects", "mood")
    op.drop_column("studio_projects", "theme")
