"""Celery chart pipeline tasks."""

from datetime import date

from app.celery_app import celery_app
from app.db import ChartEntry, ChartSource, SessionLocal, get_session
from sqlalchemy import select


DEMO_ENTRIES = [
    (1, "Midnight Echo", "Luna Rivers"),
    (2, "Neon Pulse", "Static Hearts"),
    (3, "Paper Planes", "The Draft Kings"),
    (4, "Golden Hour", "Saffron Sky"),
    (5, "Low Tide", "Coastal Ghost"),
]


def _run_pipeline_for_source(session, source: ChartSource, week: date) -> bool:
    existing = session.execute(
        select(ChartEntry).where(ChartEntry.source_id == source.id, ChartEntry.week_date == week)
    ).scalars().first()
    if existing:
        return False
    for position, title, artist in DEMO_ENTRIES:
        session.add(
            ChartEntry(
                source_id=source.id,
                position=position,
                title=title,
                artist=artist,
                week_date=week,
                is_demo=True,
            )
        )
    return True


@celery_app.task(name="charts.refresh_pipeline")
def refresh_chart_pipeline(week_date: str | None = None):
    """Refresh mock chart sources for the current week."""
    week = date.fromisoformat(week_date) if week_date else date.today()
    refreshed = 0
    with get_session() as session:
        sources = session.execute(select(ChartSource)).scalars().all()
        for source in sources:
            if source.is_mock and _run_pipeline_for_source(session, source, week):
                refreshed += 1
    return {"week_date": week.isoformat(), "refreshed": refreshed}
