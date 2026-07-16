"""E2E #8: Cross-user S3 / media access denied."""

import uuid

import pytest

from conftest import dev_login


@pytest.mark.e2e
def test_presigned_url_denied_for_unknown_asset(client, auth_headers):
    fake_asset_id = uuid.uuid4()
    denied = client.get(
        f"/api/v1/media/assets/{fake_asset_id}/presigned-url",
        headers=auth_headers,
    )
    assert denied.status_code == 404


@pytest.mark.e2e
def test_upload_part_denied_for_other_users_upload(client, auth_headers):
    other_headers, _ = dev_login(client, "admin@example.com")

    initiated = client.post(
        "/api/v1/media/uploads/initiate",
        headers=other_headers,
        json={"filename": "private.wav", "content_type": "audio/wav", "total_size": 512},
    )
    assert initiated.status_code == 201
    upload_id = initiated.json()["upload_id"]

    denied = client.post(
        f"/api/v1/media/uploads/{upload_id}/parts",
        headers=auth_headers,
        data={"part_number": 1},
        files={"file": ("part.bin", b"stolen", "application/octet-stream")},
    )
    assert denied.status_code == 404
