"""Studio lyrics CRUD and analysis tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _auth_headers(client: AsyncClient) -> dict:
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    token = login.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_project(client: AsyncClient, headers: dict) -> str:
    created = await client.post(
        "/api/v1/studio/projects",
        json={
            "title": "Lyrics Test",
            "theme": "summer",
            "mood": "upbeat",
            "genre": "pop",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


@pytest.mark.asyncio
async def test_lyric_version_crud(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    created = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        json={"content": "Line one here\nLine two near", "prompt": "test"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    version = created.json()
    assert version["version_number"] == 1
    version_id = version["id"]

    listed = await client.get(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    patched = await client.patch(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions/{version_id}",
        json={"content": "Updated line one\nLine two near"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert "Updated" in patched.json()["content"]


@pytest.mark.asyncio
async def test_lyric_fragment_patch(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    created = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        json={"content": "First line\nSecond line\nThird line"},
        headers=headers,
    )
    version_id = created.json()["id"]

    patched = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions/{version_id}/patch",
        json={"start_line": 2, "end_line": 2, "replacement": "Replaced middle"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert "Replaced middle" in patched.json()["content"]
    assert "Second line" not in patched.json()["content"]


@pytest.mark.asyncio
async def test_analyze_syllables(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/analyze-syllables",
        json={"text": "Hello world\nTesting syllables"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_syllables"] > 0
    assert body["line_count"] == 2
    assert len(body["lines"]) == 2


@pytest.mark.asyncio
async def test_analyze_rhymes(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/analyze-rhymes",
        json={"text": "Shining light\nStars so bright\nDifferent path"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rhyme_group_count"] >= 1


@pytest.mark.asyncio
async def test_assistant_message(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/assistant/messages",
        json={"content": "Suggest a chorus about stars"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "stars" in body["user_message"]
    assert len(body["assistant_message"]) > 0


@pytest.mark.asyncio
async def test_task_polling_fallback(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    task_resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/generate-lyrics",
        json={"prompt": "A short verse about rain"},
        headers=headers,
    )
    assert task_resp.status_code == 202
    task_id = task_resp.json()["id"]

    polled = await client.get(
        f"/api/v1/studio/projects/{project_id}/tasks/{task_id}",
        headers=headers,
    )
    assert polled.status_code == 200
    assert polled.json()["id"] == task_id


@pytest.mark.asyncio
async def test_lyric_version_not_found(client):
    headers = await _auth_headers(client)
    project_id = await _create_project(client, headers)

    resp = await client.patch(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions/{uuid.uuid4()}",
        json={"content": "nope"},
        headers=headers,
    )
    assert resp.status_code == 404
