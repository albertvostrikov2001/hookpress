"""AI provider failure isolation — unit/integration layer."""

import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.infrastructure.providers.base import LLMProvider
from app.main import app

DEV_EMAIL = "artist@example.com"


class FailingLLMProvider(LLMProvider):
    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        raise RuntimeError("simulated provider outage")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    return {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}


@pytest.mark.asyncio
async def test_assistant_failure_does_not_corrupt_project(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": f"Isolation {uuid.uuid4().hex[:8]}"},
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    with patch("app.application.studio_service.get_llm_provider", return_value=FailingLLMProvider()):
        failed = await client.post(
            f"/api/v1/studio/projects/{project_id}/assistant/messages",
            json={"content": "Help with chorus"},
            headers=headers,
        )
    assert failed.status_code == 500

    project = await client.get(f"/api/v1/studio/projects/{project_id}", headers=headers)
    assert project.status_code == 200
    assert project.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_lyrics_crud_works_after_llm_failure(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Post-failure lyrics"},
        headers=headers,
    )
    project_id = created.json()["id"]

    with patch("app.application.studio_service.get_llm_provider", return_value=FailingLLMProvider()):
        await client.post(
            f"/api/v1/studio/projects/{project_id}/assistant/messages",
            json={"content": "trigger failure"},
            headers=headers,
        )

    version = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        json={"content": "Manual lyrics after outage"},
        headers=headers,
    )
    assert version.status_code == 201
    assert "Manual lyrics" in version.json()["content"]
