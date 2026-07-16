"""Feed schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FeedCategoryCreate(BaseModel):
    slug: str = Field(max_length=80)
    name: str = Field(max_length=120)


class FeedCategoryResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str

    model_config = {"from_attributes": True}


class FeedTagResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str

    model_config = {"from_attributes": True}


class FeedArticleCreate(BaseModel):
    title: str = Field(max_length=300)
    body: str
    summary: str | None = None
    category_id: uuid.UUID | None = None
    slug: str | None = None
    tags: list[str] | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None


class FeedArticleResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    category_id: uuid.UUID | None
    title: str
    slug: str
    summary: str | None
    body: str
    status: str
    moderation_status: str
    seo_title: str | None
    seo_description: str | None
    seo_keywords: str | None
    view_count: int = 0
    published_at: datetime | None
    created_at: datetime
    like_count: int = 0
    bookmark_count: int = 0
    bookmarked: bool = False
    tags: list[FeedTagResponse] = []

    model_config = {"from_attributes": True}


class FeedCommentCreate(BaseModel):
    body: str
    parent_id: uuid.UUID | None = None


class FeedCommentResponse(BaseModel):
    id: uuid.UUID
    article_id: uuid.UUID
    user_id: uuid.UUID
    body: str
    parent_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RssIngestRequest(BaseModel):
    feed_url: str
    category_id: uuid.UUID | None = None


class FeedViewResponse(BaseModel):
    view_count: int


class FeedArticleListResponse(BaseModel):
    items: list[FeedArticleResponse]
    total: int
    has_more: bool
