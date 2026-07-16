"""Feed bookmarks/views/tags, chart weights, chat attachments."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260714_0009"
down_revision: Union[str, None] = "20260714_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "feed_articles",
        sa.Column("moderation_status", sa.String(length=32), server_default="APPROVED", nullable=False),
    )
    op.add_column("feed_articles", sa.Column("seo_title", sa.String(length=300), nullable=True))
    op.add_column("feed_articles", sa.Column("seo_description", sa.Text(), nullable=True))
    op.add_column("feed_articles", sa.Column("seo_keywords", sa.String(length=500), nullable=True))
    op.add_column("feed_articles", sa.Column("view_count", sa.Integer(), server_default="0", nullable=False))
    op.create_index(op.f("ix_feed_articles_moderation_status"), "feed_articles", ["moderation_status"], unique=False)

    op.create_table(
        "feed_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_feed_tags_slug"),
    )

    op.create_table(
        "feed_article_tags",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["feed_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["feed_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "tag_id"),
    )

    op.create_table(
        "feed_bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["feed_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "user_id", name="uq_feed_bookmarks_article_user"),
    )
    op.create_index(op.f("ix_feed_bookmarks_user_id"), "feed_bookmarks", ["user_id"], unique=False)

    op.create_table(
        "feed_article_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("viewer_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["feed_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "viewer_key", name="uq_feed_article_views_article_viewer"),
    )
    op.create_index(op.f("ix_feed_article_views_article_id"), "feed_article_views", ["article_id"], unique=False)

    op.add_column(
        "chart_sources",
        sa.Column("source_weights", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )

    op.add_column(
        "chat_messages",
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_chat_messages_media_asset_id",
        "chat_messages",
        "media_assets",
        ["media_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_chat_messages_media_asset_id", "chat_messages", type_="foreignkey")
    op.drop_column("chat_messages", "media_asset_id")
    op.drop_column("chart_sources", "source_weights")
    op.drop_index(op.f("ix_feed_article_views_article_id"), table_name="feed_article_views")
    op.drop_table("feed_article_views")
    op.drop_index(op.f("ix_feed_bookmarks_user_id"), table_name="feed_bookmarks")
    op.drop_table("feed_bookmarks")
    op.drop_table("feed_article_tags")
    op.drop_table("feed_tags")
    op.drop_index(op.f("ix_feed_articles_moderation_status"), table_name="feed_articles")
    op.drop_column("feed_articles", "view_count")
    op.drop_column("feed_articles", "seo_keywords")
    op.drop_column("feed_articles", "seo_description")
    op.drop_column("feed_articles", "seo_title")
    op.drop_column("feed_articles", "moderation_status")
