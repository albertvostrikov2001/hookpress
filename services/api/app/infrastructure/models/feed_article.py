"""Feed article."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FeedArticle(Base):
    __tablename__ = "feed_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feed_categories.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(300), unique=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    moderation_status: Mapped[str] = mapped_column(String(32), default="APPROVED", index=True)
    seo_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["FeedCategory | None"] = relationship(back_populates="articles", lazy="selectin")
    comments: Mapped[list["FeedComment"]] = relationship(back_populates="article", lazy="selectin")
    likes: Mapped[list["FeedLike"]] = relationship(back_populates="article", lazy="selectin")
    bookmarks: Mapped[list["FeedBookmark"]] = relationship(back_populates="article", lazy="selectin")
    views: Mapped[list["FeedArticleView"]] = relationship(back_populates="article", lazy="selectin")
    tags: Mapped[list["FeedTag"]] = relationship(
        secondary="feed_article_tags", back_populates="articles", lazy="selectin"
    )
