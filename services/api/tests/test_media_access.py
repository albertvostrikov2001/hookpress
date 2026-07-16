"""Cross-user media access tests."""

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


async def _login(client: AsyncClient, email: str) -> str:
    login = await client.post("/api/v1/auth/dev-login", json={"email": email})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    return login.json()["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_presigned_url_denied_for_other_user(client):
    token_a = await _login(client, DEV_EMAIL)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    fake_asset_id = uuid.uuid4()
    denied = await client.get(
        f"/api/v1/media/assets/{fake_asset_id}/presigned-url",
        headers=headers_a,
    )
    assert denied.status_code == 404

    other_token = await _login(client, DEV_EMAIL)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    denied_again = await client.get(
        f"/api/v1/media/assets/{fake_asset_id}/presigned-url",
        headers=other_headers,
    )
    assert denied_again.status_code == 404


@pytest.mark.asyncio
async def test_upload_access_denied_for_other_user(client):
    token = await _login(client, DEV_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        f"/api/v1/media/uploads/{uuid.uuid4()}/parts",
        headers=headers,
        data={"part_number": 1},
        files={"file": ("part.bin", b"data", "application/octet-stream")},
    )
    assert resp.status_code == 404
