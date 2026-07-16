"""Mock chart pipeline with labeled demo data, Redis cache, and position dynamics."""

import json
import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core import redis as redis_core
from app.infrastructure.models.chart_entry import ChartEntry
from app.infrastructure.models.chart_source import ChartSource

DEMO_ENTRIES = [
    (1, "Midnight Echo", "Luna Rivers"),
    (2, "Neon Pulse", "Static Hearts"),
    (3, "Paper Planes", "The Draft Kings"),
    (4, "Golden Hour", "Saffron Sky"),
    (5, "Low Tide", "Coastal Ghost"),
]

# Previous-week positions for demo dynamics (title, artist) -> position
DEMO_PREVIOUS_POSITIONS = {
    ("Midnight Echo", "Luna Rivers"): 2,
    ("Neon Pulse", "Static Hearts"): 1,
    ("Paper Planes", "The Draft Kings"): 5,
    ("Golden Hour", "Saffron Sky"): 3,
    ("Low Tide", "Coastal Ghost"): 4,
}

DEFAULT_WEIGHTS = {
    "streams": 0.45,
    "downloads": 0.25,
    "social": 0.15,
    "editorial": 0.15,
}

CHART_CACHE_TTL_SECONDS = 300


class ChartService:
    def _cache_key(self, source_slug: str, week: date) -> str:
        return f"chart:{source_slug}:{week.isoformat()}"

    async def invalidate_cache(self, source_slug: str, week: date | None = None) -> None:
        try:
            if week is not None:
                await redis_core.redis_client.delete(self._cache_key(source_slug, week))
                return
            pattern = f"chart:{source_slug}:*"
            async for key in redis_core.redis_client.scan_iter(match=pattern):
                await redis_core.redis_client.delete(key)
        except Exception:
            return

    async def ensure_mock_source(self, db: AsyncSession) -> ChartSource:
        result = await db.execute(select(ChartSource).where(ChartSource.slug == "demo-top-40"))
        source = result.scalar_one_or_none()
        if source:
            return source
        source = ChartSource(
            name="Demo Top 40",
            slug="demo-top-40",
            is_mock=True,
            source_weights=dict(DEFAULT_WEIGHTS),
        )
        db.add(source)
        await db.flush()
        return source

    async def seed_previous_week(self, db: AsyncSession, *, week_date: date | None = None) -> ChartSource:
        """Seed prior-week entries so position dynamics are visible in the UI."""
        source = await self.ensure_mock_source(db)
        week = week_date or (date.today() - timedelta(days=7))
        existing = await db.execute(
            select(ChartEntry).where(ChartEntry.source_id == source.id, ChartEntry.week_date == week)
        )
        if existing.scalars().first():
            return source

        for (title, artist), position in DEMO_PREVIOUS_POSITIONS.items():
            db.add(
                ChartEntry(
                    source_id=source.id,
                    position=position,
                    title=title,
                    artist=artist,
                    week_date=week,
                    is_demo=True,
                )
            )
        await db.flush()
        return source

    async def run_mock_pipeline(self, db: AsyncSession, *, week_date: date | None = None) -> ChartSource:
        source = await self.ensure_mock_source(db)
        week = week_date or date.today()
        existing = await db.execute(
            select(ChartEntry).where(ChartEntry.source_id == source.id, ChartEntry.week_date == week)
        )
        if existing.scalars().first():
            return source

        for position, title, artist in DEMO_ENTRIES:
            db.add(
                ChartEntry(
                    source_id=source.id,
                    position=position,
                    title=title,
                    artist=artist,
                    week_date=week,
                    is_demo=True,
                )
            )
        await db.flush()
        await self.invalidate_cache(source.slug, week)
        return source

    async def refresh_all_sources(self, db: AsyncSession, *, week_date: date | None = None) -> int:
        week = week_date or date.today()
        result = await db.execute(select(ChartSource))
        sources = list(result.scalars().all())
        refreshed = 0
        for source in sources:
            if source.is_mock:
                await self.run_mock_pipeline(db, week_date=week)
                refreshed += 1
        return refreshed

    async def update_source_weights(
        self,
        db: AsyncSession,
        *,
        source_slug: str,
        weights: dict[str, float],
    ) -> ChartSource:
        result = await db.execute(select(ChartSource).where(ChartSource.slug == source_slug))
        source = result.scalar_one_or_none()
        if source is None:
            raise AppError("chart_not_found", "Chart source not found", status_code=404)
        total = sum(weights.values())
        if total <= 0:
            raise AppError("invalid_weights", "Weights must sum to a positive value", status_code=400)
        normalized = {key: value / total for key, value in weights.items()}
        source.source_weights = normalized
        await db.flush()
        await self.invalidate_cache(source_slug)
        return source

    async def _previous_week_positions(
        self,
        db: AsyncSession,
        *,
        source_id: uuid.UUID,
        week: date,
    ) -> dict[tuple[str, str], int]:
        prev_week = week - timedelta(days=7)
        result = await db.execute(
            select(ChartEntry).where(
                ChartEntry.source_id == source_id,
                ChartEntry.week_date == prev_week,
            )
        )
        return {(entry.title, entry.artist): entry.position for entry in result.scalars().all()}

    def _entry_dynamics(
        self,
        entry: ChartEntry,
        previous_positions: dict[tuple[str, str], int],
    ) -> tuple[int | None, int | None]:
        previous_position = previous_positions.get((entry.title, entry.artist))
        if previous_position is None:
            return None, None
        position_change = previous_position - entry.position
        return previous_position, position_change

    async def get_chart(
        self,
        db: AsyncSession,
        *,
        source_slug: str = "demo-top-40",
        week_date: date | None = None,
    ) -> tuple[ChartSource, list[ChartEntry], list[tuple[int | None, int | None]]]:
        week = week_date or date.today()
        cache_key = self._cache_key(source_slug, week)
        try:
            cached = await redis_core.redis_client.get(cache_key)
        except Exception:
            cached = None
        if cached:
            payload = json.loads(cached)
            source = ChartSource(
                id=uuid.UUID(payload["source"]["id"]),
                name=payload["source"]["name"],
                slug=payload["source"]["slug"],
                is_mock=payload["source"]["is_mock"],
                source_weights=payload["source"]["source_weights"],
            )
            entries: list[ChartEntry] = []
            dynamics: list[tuple[int | None, int | None]] = []
            for item in payload["entries"]:
                entries.append(
                    ChartEntry(
                        id=uuid.UUID(item["id"]),
                        source_id=source.id,
                        position=item["position"],
                        title=item["title"],
                        artist=item["artist"],
                        week_date=date.fromisoformat(item["week_date"]),
                        is_demo=item["is_demo"],
                    )
                )
                dynamics.append((item.get("previous_position"), item.get("position_change")))
            return source, entries, dynamics

        result = await db.execute(select(ChartSource).where(ChartSource.slug == source_slug))
        source = result.scalar_one_or_none()
        if source is None:
            raise AppError("chart_not_found", "Chart source not found", status_code=404)

        result = await db.execute(
            select(ChartEntry)
            .where(ChartEntry.source_id == source.id, ChartEntry.week_date == week)
            .order_by(ChartEntry.position)
        )
        entries = list(result.scalars().all())
        if not entries and source.is_mock:
            await self.run_mock_pipeline(db, week_date=week)
            result = await db.execute(
                select(ChartEntry)
                .where(ChartEntry.source_id == source.id, ChartEntry.week_date == week)
                .order_by(ChartEntry.position)
            )
            entries = list(result.scalars().all())

        previous_positions = await self._previous_week_positions(db, source_id=source.id, week=week)
        dynamics = [self._entry_dynamics(entry, previous_positions) for entry in entries]

        cache_payload = {
            "source": {
                "id": str(source.id),
                "name": source.name,
                "slug": source.slug,
                "is_mock": source.is_mock,
                "source_weights": source.source_weights or {},
            },
            "entries": [
                {
                    "id": str(entry.id),
                    "position": entry.position,
                    "title": entry.title,
                    "artist": entry.artist,
                    "week_date": entry.week_date.isoformat(),
                    "is_demo": entry.is_demo,
                    "previous_position": prev_pos,
                    "position_change": pos_change,
                }
                for entry, (prev_pos, pos_change) in zip(entries, dynamics, strict=True)
            ],
        }
        try:
            await redis_core.redis_client.setex(cache_key, CHART_CACHE_TTL_SECONDS, json.dumps(cache_payload))
        except Exception:
            pass
        return source, entries, dynamics

    async def list_sources(self, db: AsyncSession) -> list[ChartSource]:
        result = await db.execute(select(ChartSource).order_by(ChartSource.name))
        return list(result.scalars().all())

    async def get_source(self, db: AsyncSession, *, source_slug: str) -> ChartSource:
        result = await db.execute(select(ChartSource).where(ChartSource.slug == source_slug))
        source = result.scalar_one_or_none()
        if source is None:
            from app.core.errors import AppError

            raise AppError("chart_source_not_found", "Chart source not found", status_code=404)
        return source

    def compute_week_start(self, today: date | None = None) -> date:
        today = today or date.today()
        return today - timedelta(days=today.weekday())


chart_service = ChartService()
