"""Office API schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TrackResponse(BaseModel):
    id: uuid.UUID
    title: str
    position: int
    media_asset_id: uuid.UUID | None
    lyric_version_id: uuid.UUID | None
    isrc: str | None = None
    is_test_code: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ReleaseResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    release_type: str = "SINGLE"
    contributors: list | None = None
    explicit: bool = False
    release_date: date | None = None
    cover_asset_id: uuid.UUID | None = None
    upc: str | None = None
    is_test_code: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OfficeProjectResponse(BaseModel):
    id: uuid.UUID
    studio_project_id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    tracks: list[TrackResponse] = []
    releases: list[ReleaseResponse] = []

    model_config = {"from_attributes": True}


class OfficeProjectListResponse(BaseModel):
    items: list[OfficeProjectResponse]
    total: int
    page: int
    page_size: int


class ReleaseCreate(BaseModel):
    title: str = Field(max_length=200)
    release_type: str = "SINGLE"
    contributors: list[dict] | None = None
    explicit: bool = False
    release_date: date | None = None
    cover_asset_id: uuid.UUID | None = None
    upc: str | None = Field(default=None, max_length=32)
    is_test_code: bool = False


class ReleaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    release_type: str | None = None
    contributors: list[dict] | None = None
    explicit: bool | None = None
    release_date: date | None = None
    cover_asset_id: uuid.UUID | None = None
    upc: str | None = Field(default=None, max_length=32)
    is_test_code: bool | None = None


class TrackCreate(BaseModel):
    title: str = Field(max_length=200)
    media_asset_id: uuid.UUID | None = None
    isrc: str | None = Field(default=None, max_length=32)
    is_test_code: bool = False


class TrackUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    media_asset_id: uuid.UUID | None = None
    isrc: str | None = Field(default=None, max_length=32)
    is_test_code: bool | None = None


class SubmitReleaseResponse(BaseModel):
    release_id: uuid.UUID
    status: str
    scoring_task_id: str | None = None


class ScoringReportResponse(BaseModel):
    id: uuid.UUID
    release_id: uuid.UUID
    track_id: uuid.UUID | None
    bpm: float | None
    energy: float | None
    danceability: float | None
    raw_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DistributionJobResponse(BaseModel):
    id: uuid.UUID
    release_id: uuid.UUID
    provider: str
    status: str
    external_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
