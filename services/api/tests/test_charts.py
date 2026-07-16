"""Chart cache and position dynamics tests."""

import pytest
from httpx import AsyncClient

from app.application.chart_service import chart_service
from app.core.database import SessionLocal


@pytest.mark.asyncio
async def test_chart_position_dynamics(client: AsyncClient):
    async with SessionLocal() as session:
        await chart_service.seed_previous_week(session)
        await chart_service.run_mock_pipeline(session)
        await session.commit()

    response = await client.get("/api/v1/charts/demo-top-40")
    assert response.status_code == 200
    entries = response.json()["entries"]
    assert len(entries) >= 1
    with_dynamics = [entry for entry in entries if entry.get("position_change") is not None]
    assert with_dynamics, "Expected at least one entry with week-over-week position change"


@pytest.mark.asyncio
async def test_chart_redis_cache_hit(client: AsyncClient):
    async with SessionLocal() as session:
        await chart_service.run_mock_pipeline(session)
        await session.commit()

    first = await client.get("/api/v1/charts/demo-top-40")
    assert first.status_code == 200

    second = await client.get("/api/v1/charts/demo-top-40")
    assert second.status_code == 200
    assert second.json()["entries"] == first.json()["entries"]
