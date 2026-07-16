"""Feed routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sa_inspect

from app.api.deps import get_current_user, optional_current_user
from app.application.feed_service import feed_service
from app.core.database import get_db
from app.schemas.feed import (
    FeedArticleCreate,
    FeedArticleListResponse,
    FeedArticleResponse,
    FeedCategoryCreate,
    FeedCategoryResponse,
    FeedCommentCreate,
    FeedCommentResponse,
    FeedTagResponse,
    FeedViewResponse,
    RssIngestRequest,
)

router = APIRouter(prefix="/feed", tags=["feed"])


def _article_tags(article) -> list[FeedTagResponse]:
    state = sa_inspect(article)
    if "tags" in state.unloaded:
        return []
    return [FeedTagResponse.model_validate(t) for t in (article.tags or [])]


async def _article_response(
    db: AsyncSession,
    article,
    *,
    user_id: uuid.UUID | None = None,
) -> FeedArticleResponse:
    likes = await feed_service.like_count(db, article.id)
    bookmarks = await feed_service.bookmark_count(db, article.id)
    bookmarked = False
    if user_id:
        bookmarked = await feed_service.is_bookmarked(db, article_id=article.id, user_id=user_id)
    return FeedArticleResponse(
        id=article.id,
        author_id=article.author_id,
        category_id=article.category_id,
        title=article.title,
        slug=article.slug,
        summary=article.summary,
        body=article.body,
        status=article.status,
        moderation_status=getattr(article, "moderation_status", "PENDING"),
        seo_title=getattr(article, "seo_title", None),
        seo_description=getattr(article, "seo_description", None),
        seo_keywords=getattr(article, "seo_keywords", None),
        view_count=getattr(article, "view_count", 0) or 0,
        published_at=article.published_at,
        created_at=article.created_at,
        like_count=likes,
        bookmark_count=bookmarks,
        bookmarked=bookmarked,
        tags=_article_tags(article),
    )


@router.get("/tags", response_model=list[FeedTagResponse])
async def list_tags(db: Annotated[AsyncSession, Depends(get_db)]):
    tags = await feed_service.list_tags(db)
    return [FeedTagResponse.model_validate(t) for t in tags]


@router.get("/categories", response_model=list[FeedCategoryResponse])
async def list_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await feed_service.list_categories(db)
    return [FeedCategoryResponse.model_validate(c) for c in categories]


@router.post("/categories", response_model=FeedCategoryResponse)
async def create_category(
    body: FeedCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    category = await feed_service.create_category(db, slug=body.slug, name=body.name)
    await db.commit()
    return category


@router.post("/articles", response_model=FeedArticleResponse)
async def create_article(
    body: FeedArticleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    article = await feed_service.create_article(
        db,
        author_id=current.user_id,
        title=body.title,
        body=body.body,
        summary=body.summary,
        category_id=body.category_id,
        slug=body.slug,
        tags=body.tags,
        seo_title=body.seo_title,
        seo_description=body.seo_description,
        seo_keywords=body.seo_keywords,
    )
    await db.commit()
    return await _article_response(db, article, user_id=current.user_id)


@router.post("/articles/{article_id}/publish", response_model=FeedArticleResponse)
async def publish_article(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    article = await feed_service.publish_article(db, current.user_id, article_id)
    await db.commit()
    return await _article_response(db, article, user_id=current.user_id)


@router.get("/articles", response_model=FeedArticleListResponse)
async def list_articles(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current=Depends(optional_current_user),
):
    articles = await feed_service.list_published(
        db, category_slug=category, tag_slug=tag, limit=limit, offset=offset
    )
    total = await feed_service.count_published(db, category_slug=category, tag_slug=tag)
    user_id = current.user_id if current else None
    items = [await _article_response(db, article, user_id=user_id) for article in articles]
    return FeedArticleListResponse(items=items, total=total, has_more=offset + len(items) < total)


@router.get("/articles/{article_id}", response_model=FeedArticleResponse)
async def get_article(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(optional_current_user),
):
    article = await feed_service.get_article(db, article_id)
    user_id = current.user_id if current else None
    return await _article_response(db, article, user_id=user_id)


@router.post("/articles/{article_id}/view", response_model=FeedViewResponse)
async def record_view(
    article_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(optional_current_user),
):
    user_id = current.user_id if current else None
    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")
    viewer_key = feed_service.viewer_key(user_id=user_id, ip=ip, user_agent=ua)
    view_count = await feed_service.record_view(
        db, article_id=article_id, user_id=user_id, viewer_key=viewer_key
    )
    await db.commit()
    return FeedViewResponse(view_count=view_count)


@router.get("/articles/{article_id}/comments", response_model=list[FeedCommentResponse])
async def list_comments(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=100),
):
    comments = await feed_service.list_comments(db, article_id=article_id, limit=limit)
    return [FeedCommentResponse.model_validate(c) for c in comments]


@router.post("/articles/{article_id}/comments", response_model=FeedCommentResponse)
async def add_comment(
    article_id: uuid.UUID,
    body: FeedCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    comment = await feed_service.add_comment(
        db,
        article_id=article_id,
        user_id=current.user_id,
        body=body.body,
        parent_id=body.parent_id,
    )
    await db.commit()
    return comment


@router.post("/articles/{article_id}/like")
async def toggle_like(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    liked = await feed_service.toggle_like(db, article_id=article_id, user_id=current.user_id)
    await db.commit()
    return {"liked": liked}


@router.post("/articles/{article_id}/bookmark")
async def toggle_bookmark(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    bookmarked = await feed_service.toggle_bookmark(db, article_id=article_id, user_id=current.user_id)
    await db.commit()
    return {"bookmarked": bookmarked}


@router.post("/ingest/rss")
async def ingest_rss(
    body: RssIngestRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
):
    result = await feed_service.ingest_rss(
        db,
        feed_url=body.feed_url,
        author_id=current.user_id,
        category_id=body.category_id,
    )
    await db.commit()
    return result
