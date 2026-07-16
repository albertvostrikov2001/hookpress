"""Chart schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ChartSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_mock: bool
    source_weights: dict[str, float] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class ChartEntryResponse(BaseModel):
    id: uuid.UUID
    position: int
    title: str
    artist: str
    week_date: date
    is_demo: bool
    previous_position: int | None = None
    position_change: int | None = Field(
        default=None,
        description="Positive means moved up in chart (lower rank number)",
    )

    model_config = {"from_attributes": True}


class ChartResponse(BaseModel):
    source: ChartSourceResponse
    week_date: date
    entries: list[ChartEntryResponse]


class ChartSourceWeightsUpdate(BaseModel):
    weights: dict[str, float]
