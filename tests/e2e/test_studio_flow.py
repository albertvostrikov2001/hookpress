"""E2E #2: Text → lyrics → audio → Office handoff."""

import time
import uuid

import pytest


@pytest.mark.e2e
def test_studio_full_pipeline_to_office(client, auth_headers):
    title = f"E2E Pipeline {uuid.uuid4().hex[:8]}"
    create = client.post(
        "/api/v1/studio/projects",
        json={
            "title": title,
            "theme": "summer nights",
            "mood": "upbeat",
            "genre": "pop",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    project_id = create.json()["id"]

    lyrics = client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/versions",
        json={
            "content": "Under neon skies we drive\nChasing dreams that feel alive",
            "prompt": "e2e chorus",
        },
        headers=auth_headers,
    )
    assert lyrics.status_code == 201, lyrics.text
    version_id = lyrics.json()["id"]

    syllables = client.post(
        f"/api/v1/studio/projects/{project_id}/lyrics/analyze-syllables",
        json={"lyric_version_id": version_id},
        headers=auth_headers,
    )
    assert syllables.status_code == 200
    assert syllables.json()["line_count"] >= 2

    audio_task = client.post(
        f"/api/v1/studio/projects/{project_id}/generate-audio",
        json={"lyric_version_id": version_id},
        headers=auth_headers,
    )
    assert audio_task.status_code == 202, audio_task.text
    task_id = audio_task.json()["id"]

    deadline = time.time() + 15
    task_status = "PENDING"
    while time.time() < deadline:
        polled = client.get(
            f"/api/v1/studio/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers,
        )
        assert polled.status_code == 200
        task_status = polled.json()["status"]
        if task_status in {"SUCCEEDED", "FAILED"}:
            break
        time.sleep(0.5)

    get_project = client.get(f"/api/v1/studio/projects/{project_id}", headers=auth_headers)
    assert get_project.status_code == 200
    assert get_project.json()["title"] == title

    idem_key = f"e2e-send-{uuid.uuid4()}"
    send_headers = {**auth_headers, "Idempotency-Key": idem_key}
    first = client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers=send_headers,
    )
    second = client.post(
        f"/api/v1/studio/projects/{project_id}/send-to-office",
        headers=send_headers,
    )
    assert first.status_code == 202, first.text
    assert second.status_code == 202, second.text
    assert first.json()["idempotent"] is False
    assert second.json()["idempotent"] is True
    assert first.json()["office_project_id"] == second.json()["office_project_id"]
