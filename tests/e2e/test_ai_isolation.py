"""E2E #12: AI provider failure does not break unrelated studio endpoints."""

import uuid

import pytest


@pytest.mark.e2e
def test_project_survives_pending_ai_task(client, auth_headers):
    """Pending AI task must not block project reads (isolation at HTTP layer)."""
    created = client.post(
        "/api/v1/studio/projects",
        json={"title": f"Pending Task {uuid.uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    task = client.post(
        f"/api/v1/studio/projects/{project_id}/generate-lyrics",
        json={"prompt": "A verse about resilience"},
        headers=auth_headers,
    )
    assert task.status_code == 202

    fetched = client.get(f"/api/v1/studio/projects/{project_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == project_id


@pytest.mark.e2e
def test_manual_lyrics_after_ai_task(client, auth_headers):
    """Lyrics CRUD remains available regardless of async AI task state."""
    created = client.post(
        "/api/v1/studio/projects",
        json={"title": f"Manual Lyrics {uuid.uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    project_id = created.json()["id"]

    client.post(
        f"/api/v1/studio/projects/{project_id}/generate-lyrics",
        json={"prompt": "trigger async task"},
        headers=auth_headers,
    )

    lyrics = client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        json={"content": "Hand-written lyrics\nIndependent of AI"},
        headers=auth_headers,
    )
    assert lyrics.status_code == 201
    assert "Hand-written" in lyrics.json()["content"]
