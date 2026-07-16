"""Kwork cover asset."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260715_0013"
down_revision: Union[str, None] = "20260714_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "kworks",
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_kworks_cover_asset_id",
        "kworks",
        "media_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_kworks_cover_asset_id"), "kworks", ["cover_asset_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_kworks_cover_asset_id"), table_name="kworks")
    op.drop_constraint("fk_kworks_cover_asset_id", "kworks", type_="foreignkey")
    op.drop_column("kworks", "cover_asset_id")
