"""Admin-only endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sa_inspect

from app.api.deps import CurrentUser, require_roles
from app.application.audit_read_service import audit_read_service
from app.application.auth_service import auth_service
from app.application.chart_service import chart_service
from app.application.feed_service import feed_service
from app.core.database import get_db
from app.domain.auth.roles import Role
from app.schemas.audit import AuditLogListResponse, AuditLogResponse
from app.schemas.auth import SetUserRolesRequest, UserResponse
from app.schemas.charts import ChartSourceResponse, ChartSourceWeightsUpdate
from app.schemas.feed import FeedArticleResponse, FeedTagResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=[r.role for r in user.roles],
    )


async def _feed_article_response(db: AsyncSession, article) -> FeedArticleResponse:
    likes = await feed_service.like_count(db, article.id)
    bookmarks = await feed_service.bookmark_count(db, article.id)
    state = sa_inspect(article)
    tag_models = [] if "tags" in state.unloaded else [FeedTagResponse.model_validate(t) for t in article.tags]
    return FeedArticleResponse(
        **FeedArticleResponse.model_validate(article).model_dump(
            exclude={"like_count", "bookmark_count", "bookmarked", "tags"}
        ),
        like_count=likes,
        bookmark_count=bookmarks,
        bookmarked=False,
        tags=tag_models,
    )


@router.get("/ping")
async def admin_ping(user: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]):
    return {"status": "ok", "admin": str(user.user_id)}


@router.post("/users/{user_id}/roles", response_model=UserResponse)
async def set_user_roles(
    user_id: uuid.UUID,
    body: SetUserRolesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))],
):
    user = await auth_service.set_user_roles(
        db,
        user_id=user_id,
        roles=body.roles,
        actor_user_id=admin.user_id,
    )
    return _user_response(user)


@router.post("/feed/articles/{article_id}/approve", response_model=FeedArticleResponse)
async def approve_feed_article(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
):
    article = await feed_service.approve_article(db, article_id)
    await db.commit()
    return await _feed_article_response(db, article)


@router.post("/feed/articles/{article_id}/reject", response_model=FeedArticleResponse)
async def reject_feed_article(
    article_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
):
    article = await feed_service.reject_article(db, article_id)
    await db.commit()
    return await _feed_article_response(db, article)


@router.patch("/charts/sources/{slug}/weights", response_model=ChartSourceResponse)
async def update_chart_source_weights(
    slug: str,
    body: ChartSourceWeightsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))],
):
    source = await chart_service.update_source_weights(db, source_slug=slug, weights=body.weights)
    await db.commit()
    return source


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    action_prefix: str | None = Query(default=None),
):
    logs, total = await audit_read_service.list_logs(
        db, limit=limit, offset=offset, action_prefix=action_prefix
    )
    items = [AuditLogResponse.model_validate(log) for log in logs]
    return AuditLogListResponse(items=items, total=total, has_more=offset + len(items) < total)
