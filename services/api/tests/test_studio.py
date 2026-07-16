"""Studio flow tests."""

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


@pytest.mark.asyncio
async def test_create_and_get_studio_project(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Test Song", "description": "A demo track"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["title"] == "Test Song"
    assert body["status"] == "ACTIVE"

    fetched = await client.get(f"/api/v1/studio/projects/{body['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


@pytest.mark.asyncio
async def test_generate_lyrics_creates_task(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Lyrics Project"},
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    task_resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/generate-lyrics",
        json={"prompt": "Write a chorus about summer nights"},
        headers=headers,
    )
    assert task_resp.status_code == 202, task_resp.text
    task = task_resp.json()
    assert task["task_type"] == "GENERATE_LYRICS"
    assert task["status"] in {"PENDING", "PROCESSING", "SUCCEEDED"}


@pytest.mark.asyncio
async def test_send_to_office_idempotent(client):
    headers = await _auth_headers(client)
    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Office Handoff"},
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]
    idem = f"test-{uuid.uuid4()}"

    first = await client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers={**headers, "Idempotency-Key": idem},
    )
    assert first.status_code == 202, first.text
    first_body = first.json()
    assert first_body["idempotent"] is False

    second = await client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers={**headers, "Idempotency-Key": idem},
    )
    assert second.status_code == 202
    second_body = second.json()
    assert second_body["idempotent"] is True
    assert second_body["office_project_id"] == first_body["office_project_id"]


@pytest.mark.asyncio
async def test_studio_project_not_found_for_other_user(client):
    headers = await _auth_headers(client)
    other = await client.get(f"/api/v1/studio/projects/{uuid.uuid4()}", headers=headers)
    assert other.status_code == 404
