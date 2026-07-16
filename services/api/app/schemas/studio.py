"""Studio API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateStudioProjectRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    theme: str | None = Field(default=None, max_length=200)
    mood: str | None = Field(default=None, max_length=100)
    genre: str | None = Field(default=None, max_length=100)
    structure_json: dict[str, Any] | None = None


class UpdateStudioProjectRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    theme: str | None = Field(default=None, max_length=200)
    mood: str | None = Field(default=None, max_length=100)
    genre: str | None = Field(default=None, max_length=100)
    structure_json: dict[str, Any] | None = None


class LyricVersionResponse(BaseModel):
    id: uuid.UUID
    version_number: int
    content: str
    prompt: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateLyricVersionRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    prompt: str | None = Field(default=None, max_length=5000)


class PatchLyricVersionRequest(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=50000)
    prompt: str | None = Field(default=None, max_length=5000)


class PatchLyricFragmentRequest(BaseModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    replacement: str = Field(max_length=10000)


class AnalyzeTextRequest(BaseModel):
    text: str | None = Field(default=None, max_length=50000)
    lyric_version_id: uuid.UUID | None = None


class SyllableAnalysisResponse(BaseModel):
    total_syllables: int
    line_count: int
    average_syllables_per_line: float
    lines: list[dict[str, Any]]


class RhymeAnalysisResponse(BaseModel):
    rhyme_group_count: int
    rhyme_groups: list[dict[str, Any]]
    line_endings: dict[int, str]
    unrhymed_lines: list[int]


class AssistantMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class AssistantMessageResponse(BaseModel):
    user_message: str
    assistant_message: str
    message_id: uuid.UUID


class AiTaskResponse(BaseModel):
    id: uuid.UUID
    task_type: str
    status: str
    celery_task_id: str | None
    result_payload: dict | None
    result_metadata: dict | None = None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class StudioProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    theme: str | None = None
    mood: str | None = None
    genre: str | None = None
    structure_json: dict | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    lyric_versions: list[LyricVersionResponse] = []
    ai_tasks: list[AiTaskResponse] = []

    model_config = {"from_attributes": True}


class GenerateLyricsRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)


class GenerateAudioRequest(BaseModel):
    lyric_version_id: uuid.UUID | None = None


class GenerateWaveformRequest(BaseModel):
    audio_task_id: uuid.UUID | None = None


class PresignedAudioResponse(BaseModel):
    url: str
    expires_in: int
    media_asset_id: uuid.UUID | None = None


class SendToOfficeResponse(BaseModel):
    office_project_id: uuid.UUID
    studio_project_id: uuid.UUID
    status: str
    idempotent: bool
