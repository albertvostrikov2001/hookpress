"""Login events and auth extras."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0008"
down_revision: Union[str, None] = "20260714_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_events_email"), "login_events", ["email"], unique=False)
    op.create_index(op.f("ix_login_events_method"), "login_events", ["method"], unique=False)
    op.create_index(op.f("ix_login_events_user_id"), "login_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_login_events_user_id"), table_name="login_events")
    op.drop_index(op.f("ix_login_events_method"), table_name="login_events")
    op.drop_index(op.f("ix_login_events_email"), table_name="login_events")
    op.drop_table("login_events")
