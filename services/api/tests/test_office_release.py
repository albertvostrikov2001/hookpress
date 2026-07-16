"""Office release flow tests."""

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
async def test_release_builder_and_ready(client):
    headers = await _auth_headers(client)

    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Release Builder Song"},
        headers=headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    office_resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers={**headers, "Idempotency-Key": f"release-{uuid.uuid4()}"},
    )
    assert office_resp.status_code == 202
    office_project_id = office_resp.json()["office_project_id"]

    projects = await client.get("/api/v1/office/projects", headers=headers)
    assert projects.status_code == 200
    project = next(p for p in projects.json()["items"] if p["id"] == office_project_id)
    release_id = project["releases"][0]["id"]

    updated = await client.patch(
        f"/api/v1/office/releases/{release_id}",
        headers=headers,
        json={
            "title": "My Single",
            "release_type": "SINGLE",
            "explicit": True,
            "upc": "TEST-UPC-001",
            "is_test_code": True,
            "contributors": [{"name": "Demo Artist", "role": "performer"}],
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "My Single"
    assert body["release_type"] == "SINGLE"
    assert body["is_test_code"] is True

    track = await client.post(
        f"/api/v1/office/releases/{release_id}/tracks",
        headers=headers,
        json={"title": "Track 1", "isrc": "TEST-ISRC-001", "is_test_code": True},
    )
    assert track.status_code == 201
    assert track.json()["isrc"] == "TEST-ISRC-001"

    ready_fail = await client.post(
        f"/api/v1/office/projects/{office_project_id}/ready",
        headers=headers,
    )
    assert ready_fail.status_code == 400


@pytest.mark.asyncio
async def test_scoring_report_endpoint(client):
    headers = await _auth_headers(client)

    created = await client.post(
        "/api/v1/studio/projects",
        json={"title": "Scoring Report Song"},
        headers=headers,
    )
    project_id = created.json()["id"]
    office_resp = await client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers={**headers, "Idempotency-Key": f"score-{uuid.uuid4()}"},
    )
    release_id = office_resp.json().get("release_id") or None
    if not release_id:
        projects = await client.get("/api/v1/office/projects", headers=headers)
        project = next(
            p for p in projects.json()["items"] if p["id"] == office_resp.json()["office_project_id"]
        )
        release_id = project["releases"][0]["id"]

    reports = await client.get(
        f"/api/v1/office/releases/{release_id}/scoring-report",
        headers=headers,
    )
    assert reports.status_code == 200
    assert isinstance(reports.json(), list)
