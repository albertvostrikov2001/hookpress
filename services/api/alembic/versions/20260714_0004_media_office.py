"""Media and Office tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0004"
down_revision: Union[str, None] = "20260714_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

office_project_status = postgresql.ENUM(
    "DRAFT_IN_STUDIO",
    "DRAFT_IN_OFFICE",
    "READY_FOR_RELEASE",
    name="office_project_status",
    create_type=False,
)

release_status = postgresql.ENUM(
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


def upgrade() -> None:
    office_project_status.create(op.get_bind(), checkfirst=True)
    release_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bucket", sa.String(length=128), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bucket", "object_key", name="uq_media_assets_bucket_key"),
    )
    op.create_index(op.f("ix_media_assets_user_id"), "media_assets", ["user_id"], unique=False)

    op.create_table(
        "media_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="INITIATED"),
        sa.Column("s3_upload_id", sa.String(length=255), nullable=True),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("bucket", sa.String(length=128), nullable=False),
        sa.Column("total_size", sa.BigInteger(), nullable=True),
        sa.Column("parts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_uploads_user_id"), "media_uploads", ["user_id"], unique=False)

    op.create_table(
        "office_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("studio_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", office_project_status, nullable=False, server_default="DRAFT_IN_OFFICE"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["studio_project_id"], ["studio_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("studio_project_id", name="uq_office_projects_studio_project"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_office_projects_idempotency"),
    )
    op.create_index(op.f("ix_office_projects_user_id"), "office_projects", ["user_id"], unique=False)

    op.create_table(
        "tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("office_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lyric_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lyric_version_id"], ["lyric_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["office_project_id"], ["office_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tracks_office_project_id"), "tracks", ["office_project_id"], unique=False)

    op.create_table(
        "releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("office_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", release_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["office_project_id"], ["office_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_releases_office_project_id"), "releases", ["office_project_id"], unique=False)
    op.create_index(op.f("ix_releases_status"), "releases", ["status"], unique=False)

    op.create_table(
        "distribution_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_distribution_jobs_release_id"), "distribution_jobs", ["release_id"], unique=False)

    op.create_table(
        "scoring_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bpm", sa.Float(), nullable=True),
        sa.Column("energy", sa.Float(), nullable=True),
        sa.Column("danceability", sa.Float(), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scoring_reports_release_id"), "scoring_reports", ["release_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scoring_reports_release_id"), table_name="scoring_reports")
    op.drop_table("scoring_reports")
    op.drop_index(op.f("ix_distribution_jobs_release_id"), table_name="distribution_jobs")
    op.drop_table("distribution_jobs")
    op.drop_index(op.f("ix_releases_status"), table_name="releases")
    op.drop_index(op.f("ix_releases_office_project_id"), table_name="releases")
    op.drop_table("releases")
    op.drop_index(op.f("ix_tracks_office_project_id"), table_name="tracks")
    op.drop_table("tracks")
    op.drop_index(op.f("ix_office_projects_user_id"), table_name="office_projects")
    op.drop_table("office_projects")
    op.drop_index(op.f("ix_media_uploads_user_id"), table_name="media_uploads")
    op.drop_table("media_uploads")
    op.drop_index(op.f("ix_media_assets_user_id"), table_name="media_assets")
    op.drop_table("media_assets")
    release_status.drop(op.get_bind(), checkfirst=True)
    office_project_status.drop(op.get_bind(), checkfirst=True)
