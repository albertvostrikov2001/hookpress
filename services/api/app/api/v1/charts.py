"""Chart routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.chart_service import chart_service
from app.core.database import get_db
from app.schemas.charts import ChartEntryResponse, ChartResponse, ChartSourceResponse

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/sources", response_model=list[ChartSourceResponse])
async def list_sources(db: Annotated[AsyncSession, Depends(get_db)]):
    return await chart_service.list_sources(db)


@router.get("/sources/{slug}", response_model=ChartSourceResponse)
async def get_chart_source(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await chart_service.get_source(db, source_slug=slug)


@router.post("/pipeline/run", response_model=ChartSourceResponse)
async def run_pipeline(
    db: Annotated[AsyncSession, Depends(get_db)],
    current=Depends(get_current_user),
    week: date | None = Query(default=None),
):
    source = await chart_service.run_mock_pipeline(db, week_date=week)
    await db.commit()
    return source


@router.get("/{source_slug}", response_model=ChartResponse)
async def get_chart(
    source_slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    week: date | None = Query(default=None),
):
    source, entries, dynamics = await chart_service.get_chart(
        db, source_slug=source_slug, week_date=week
    )
    week_date = week or date.today()
    return ChartResponse(
        source=ChartSourceResponse.model_validate(source),
        week_date=week_date,
        entries=[
            ChartEntryResponse(
                id=entry.id,
                position=entry.position,
                title=entry.title,
                artist=entry.artist,
                week_date=entry.week_date,
                is_demo=entry.is_demo,
                previous_position=prev_pos,
                position_change=pos_change,
            )
            for entry, (prev_pos, pos_change) in zip(entries, dynamics, strict=True)
        ],
    )
