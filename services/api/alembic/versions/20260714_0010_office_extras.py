"""Office and media extras: release metadata, asset scanning, versions."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0010"
down_revision: Union[str, None] = "20260714_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

release_type = postgresql.ENUM("SINGLE", "EP", "ALBUM", name="release_type", create_type=False)
media_asset_status = postgresql.ENUM(
    "UPLOADING",
    "SCANNING",
    "READY",
    "REJECTED",
    name="media_asset_status",
    create_type=False,
)


def upgrade() -> None:
    release_type.create(op.get_bind(), checkfirst=True)
    media_asset_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "releases",
        sa.Column("release_type", release_type, nullable=False, server_default="SINGLE"),
    )
    op.add_column(
        "releases",
        sa.Column("contributors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "releases",
        sa.Column("explicit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("releases", sa.Column("release_date", sa.Date(), nullable=True))
    op.add_column(
        "releases",
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("releases", sa.Column("upc", sa.String(length=32), nullable=True))
    op.add_column(
        "releases",
        sa.Column("is_test_code", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_foreign_key(
        "fk_releases_cover_asset_id",
        "releases",
        "media_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("tracks", sa.Column("isrc", sa.String(length=32), nullable=True))
    op.add_column(
        "tracks",
        sa.Column("is_test_code", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.add_column(
        "media_assets",
        sa.Column("status", media_asset_status, nullable=False, server_default="UPLOADING"),
    )
    op.create_index(op.f("ix_media_assets_status"), "media_assets", ["status"], unique=False)

    op.create_table(
        "media_asset_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bucket", sa.String(length=128), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_asset_id", "version_number", name="uq_media_asset_versions_asset_ver"),
    )
    op.create_index(
        op.f("ix_media_asset_versions_media_asset_id"),
        "media_asset_versions",
        ["media_asset_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_media_asset_versions_media_asset_id"), table_name="media_asset_versions")
    op.drop_table("media_asset_versions")
    op.drop_index(op.f("ix_media_assets_status"), table_name="media_assets")
    op.drop_column("media_assets", "status")
    op.drop_column("tracks", "is_test_code")
    op.drop_column("tracks", "isrc")
    op.drop_constraint("fk_releases_cover_asset_id", "releases", type_="foreignkey")
    op.drop_column("releases", "is_test_code")
    op.drop_column("releases", "upc")
    op.drop_column("releases", "cover_asset_id")
    op.drop_column("releases", "release_date")
    op.drop_column("releases", "explicit")
    op.drop_column("releases", "contributors")
    op.drop_column("releases", "release_type")
    media_asset_status.drop(op.get_bind(), checkfirst=True)
    release_type.drop(op.get_bind(), checkfirst=True)
