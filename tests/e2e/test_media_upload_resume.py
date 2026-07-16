"""E2E #3: Multipart upload initiate, part upload, and list parts."""

import pytest


@pytest.mark.e2e
def test_multipart_upload_resume(client, auth_headers):
    initiated = client.post(
        "/api/v1/media/uploads/initiate",
        headers=auth_headers,
        json={"filename": "e2e-resume.wav", "content_type": "audio/wav", "total_size": 4096},
    )
    assert initiated.status_code == 201, initiated.text
    upload_id = initiated.json()["upload_id"]

    empty_parts = client.get(f"/api/v1/media/uploads/{upload_id}/parts", headers=auth_headers)
    assert empty_parts.status_code == 200
    assert empty_parts.json()["parts"] == []

    part_one = client.post(
        f"/api/v1/media/uploads/{upload_id}/parts",
        headers=auth_headers,
        data={"part_number": 1},
        files={"file": ("part1.bin", b"e2e-part-one-data", "application/octet-stream")},
    )
    assert part_one.status_code == 200, part_one.text
    assert part_one.json()["part_number"] == 1
    assert part_one.json()["etag"]

    part_two = client.post(
        f"/api/v1/media/uploads/{upload_id}/parts",
        headers=auth_headers,
        data={"part_number": 2},
        files={"file": ("part2.bin", b"e2e-part-two-data", "application/octet-stream")},
    )
    assert part_two.status_code == 200

    listed = client.get(f"/api/v1/media/uploads/{upload_id}/parts", headers=auth_headers)
    assert listed.status_code == 200
    part_numbers = [p.get("part_number", p.get("PartNumber")) for p in listed.json()["parts"]]
    assert part_numbers == [1, 2]
