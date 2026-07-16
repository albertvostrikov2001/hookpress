"""Feed CMS, RSS ingest, bookmarks, views, and moderation."""

import hashlib
import re
import uuid
from datetime import UTC, datetime
from html import unescape
from typing import Any

import feedparser
import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.infrastructure.models.feed_article import FeedArticle
from app.infrastructure.models.feed_article_view import FeedArticleView
from app.infrastructure.models.feed_bookmark import FeedBookmark
from app.infrastructure.models.feed_category import FeedCategory
from app.infrastructure.models.feed_comment import FeedComment
from app.infrastructure.models.feed_like import FeedLike
from app.infrastructure.models.feed_tag import FeedArticleTag, FeedTag
from app.infrastructure.security.ssrf import validate_public_url


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:280] or str(uuid.uuid4())


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(re.sub(r"\s+", " ", cleaned)).strip()


class FeedService:
    async def create_category(self, db: AsyncSession, *, slug: str, name: str) -> FeedCategory:
        category = FeedCategory(slug=slug, name=name)
        db.add(category)
        await db.flush()
        return category

    async def create_article(
        self,
        db: AsyncSession,
        *,
        author_id: uuid.UUID,
        title: str,
        body: str,
        summary: str | None = None,
        category_id: uuid.UUID | None = None,
        slug: str | None = None,
        tags: list[str] | None = None,
        seo_title: str | None = None,
        seo_description: str | None = None,
        seo_keywords: str | None = None,
    ) -> FeedArticle:
        article = FeedArticle(
            author_id=author_id,
            category_id=category_id,
            title=title,
            slug=slug or _slugify(title),
            summary=summary,
            body=body,
            status="DRAFT",
            moderation_status="PENDING",
            seo_title=seo_title,
            seo_description=seo_description,
            seo_keywords=seo_keywords,
        )
        db.add(article)
        await db.flush()
        if tags:
            await self._set_tags(db, article, tags)
        return article

    async def publish_article(self, db: AsyncSession, author_id: uuid.UUID, article_id: uuid.UUID) -> FeedArticle:
        article = await self._get_owned_article(db, author_id, article_id)
        if article.moderation_status == "REJECTED":
            raise AppError("moderation_rejected", "Article was rejected by moderation", status_code=409)
        article.status = "PUBLISHED"
        article.published_at = datetime.now(UTC)
        await db.flush()
        return article

    async def list_published(
        self,
        db: AsyncSession,
        *,
        category_slug: str | None = None,
        tag_slug: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[FeedArticle]:
        stmt = (
            select(FeedArticle)
            .options(selectinload(FeedArticle.tags))
            .where(
                FeedArticle.status == "PUBLISHED",
                FeedArticle.moderation_status == "APPROVED",
            )
            .order_by(FeedArticle.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if category_slug:
            stmt = stmt.join(FeedCategory).where(FeedCategory.slug == category_slug)
        if tag_slug:
            stmt = (
                stmt.join(FeedArticleTag)
                .join(FeedTag)
                .where(FeedTag.slug == tag_slug)
            )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_published(
        self,
        db: AsyncSession,
        *,
        category_slug: str | None = None,
        tag_slug: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(FeedArticle).where(
            FeedArticle.status == "PUBLISHED",
            FeedArticle.moderation_status == "APPROVED",
        )
        if category_slug:
            stmt = stmt.join(FeedCategory).where(FeedCategory.slug == category_slug)
        if tag_slug:
            stmt = (
                stmt.join(FeedArticleTag)
                .join(FeedTag)
                .where(FeedTag.slug == tag_slug)
            )
        return int((await db.execute(stmt)).scalar_one())

    async def list_tags(self, db: AsyncSession) -> list[FeedTag]:
        result = await db.execute(select(FeedTag).order_by(FeedTag.name))
        return list(result.scalars().all())

    async def list_categories(self, db: AsyncSession) -> list[FeedCategory]:
        result = await db.execute(select(FeedCategory).order_by(FeedCategory.name))
        return list(result.scalars().all())

    async def get_article(self, db: AsyncSession, article_id: uuid.UUID) -> FeedArticle:
        result = await db.execute(select(FeedArticle).where(FeedArticle.id == article_id))
        article = result.scalar_one_or_none()
        if article is None:
            raise AppError("article_not_found", "Article not found", status_code=404)
        return article

    async def add_comment(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        user_id: uuid.UUID,
        body: str,
        parent_id: uuid.UUID | None = None,
    ) -> FeedComment:
        article = await self.get_article(db, article_id)
        if article.status != "PUBLISHED" or article.moderation_status != "APPROVED":
            raise AppError("article_not_published", "Cannot comment on unpublished article", status_code=409)
        comment = FeedComment(article_id=article_id, user_id=user_id, body=body, parent_id=parent_id)
        db.add(comment)
        await db.flush()
        return comment

    async def list_comments(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        limit: int = 50,
    ) -> list[FeedComment]:
        article = await self.get_article(db, article_id)
        if article.status != "PUBLISHED" or article.moderation_status != "APPROVED":
            raise AppError("article_not_published", "Article is not published", status_code=404)
        result = await db.execute(
            select(FeedComment)
            .where(FeedComment.article_id == article_id)
            .order_by(FeedComment.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def toggle_like(self, db: AsyncSession, *, article_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(FeedLike).where(FeedLike.article_id == article_id, FeedLike.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.flush()
            return False
        db.add(FeedLike(article_id=article_id, user_id=user_id))
        await db.flush()
        return True

    async def toggle_bookmark(self, db: AsyncSession, *, article_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        await self.get_article(db, article_id)
        result = await db.execute(
            select(FeedBookmark).where(FeedBookmark.article_id == article_id, FeedBookmark.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await db.delete(existing)
            await db.flush()
            return False
        db.add(FeedBookmark(article_id=article_id, user_id=user_id))
        await db.flush()
        return True

    async def record_view(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        user_id: uuid.UUID | None,
        viewer_key: str,
    ) -> int:
        article = await self.get_article(db, article_id)
        result = await db.execute(
            select(FeedArticleView).where(
                FeedArticleView.article_id == article_id,
                FeedArticleView.viewer_key == viewer_key,
            )
        )
        if result.scalar_one_or_none() is None:
            db.add(
                FeedArticleView(
                    article_id=article_id,
                    user_id=user_id,
                    viewer_key=viewer_key,
                )
            )
            article.view_count += 1
            await db.flush()
        return article.view_count

    def viewer_key(self, *, user_id: uuid.UUID | None, ip: str | None, user_agent: str | None) -> str:
        if user_id:
            return f"user:{user_id}"
        raw = f"{ip or 'anon'}:{user_agent or 'unknown'}"
        return f"anon:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"

    async def like_count(self, db: AsyncSession, article_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(FeedLike).where(FeedLike.article_id == article_id)
        )
        return int(result.scalar_one())

    async def bookmark_count(self, db: AsyncSession, article_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.count()).select_from(FeedBookmark).where(FeedBookmark.article_id == article_id)
        )
        return int(result.scalar_one())

    async def is_bookmarked(self, db: AsyncSession, *, article_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(FeedBookmark).where(FeedBookmark.article_id == article_id, FeedBookmark.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None

    async def approve_article(self, db: AsyncSession, article_id: uuid.UUID) -> FeedArticle:
        article = await self.get_article(db, article_id)
        article.moderation_status = "APPROVED"
        await db.flush()
        return article

    async def reject_article(self, db: AsyncSession, article_id: uuid.UUID) -> FeedArticle:
        article = await self.get_article(db, article_id)
        article.moderation_status = "REJECTED"
        if article.status == "PUBLISHED":
            article.status = "DRAFT"
        await db.flush()
        return article

    async def ingest_rss(
        self,
        db: AsyncSession,
        *,
        feed_url: str,
        author_id: uuid.UUID,
        category_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        safe_url = validate_public_url(feed_url)
        async with httpx.AsyncClient(follow_redirects=False, timeout=15.0) as client:
            response = await client.get(safe_url)
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if location:
                    validate_public_url(location)
                    response = await client.get(location)
            response.raise_for_status()
            content = response.text

        parsed = feedparser.parse(content)
        ingested = 0
        for entry in parsed.entries[:50]:
            title = _strip_html(getattr(entry, "title", "") or "Untitled")
            body = _strip_html(getattr(entry, "summary", "") or getattr(entry, "description", "") or title)
            link = getattr(entry, "link", None)
            slug_base = _slugify(title)
            slug = slug_base
            suffix = 1
            while True:
                existing = await db.execute(select(FeedArticle).where(FeedArticle.slug == slug))
                if existing.scalar_one_or_none() is None:
                    break
                slug = f"{slug_base}-{suffix}"
                suffix += 1

            article = FeedArticle(
                author_id=author_id,
                category_id=category_id,
                title=title[:300],
                slug=slug,
                summary=body[:500] if body else None,
                body=body or title,
                status="PUBLISHED",
                moderation_status="PENDING",
                seo_title=title[:300],
                seo_description=(body[:500] if body else None),
                published_at=datetime.now(UTC),
            )
            if link:
                article.seo_keywords = link[:500]
            db.add(article)
            ingested += 1

        await db.flush()
        return {"status": "ok", "feed_url": feed_url, "ingested": ingested}

    async def _set_tags(self, db: AsyncSession, article: FeedArticle, tags: list[str]) -> None:
        for tag_name in tags:
            slug = _slugify(tag_name)
            result = await db.execute(select(FeedTag).where(FeedTag.slug == slug))
            tag = result.scalar_one_or_none()
            if tag is None:
                tag = FeedTag(slug=slug, name=tag_name.strip())
                db.add(tag)
                await db.flush()
            existing = await db.execute(
                select(FeedArticleTag).where(
                    FeedArticleTag.article_id == article.id,
                    FeedArticleTag.tag_id == tag.id,
                )
            )
            if existing.scalar_one_or_none() is None:
                db.add(FeedArticleTag(article_id=article.id, tag_id=tag.id))

    async def _get_owned_article(
        self, db: AsyncSession, author_id: uuid.UUID, article_id: uuid.UUID
    ) -> FeedArticle:
        result = await db.execute(
            select(FeedArticle).where(FeedArticle.id == article_id, FeedArticle.author_id == author_id)
        )
        article = result.scalar_one_or_none()
        if article is None:
            raise AppError("article_not_found", "Article not found", status_code=404)
        return article


feed_service = FeedService()
