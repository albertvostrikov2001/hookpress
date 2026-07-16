"""Media quarantine / AV scan tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.application.media_service import MediaService
from app.core.database import SessionLocal
from app.domain.office.enums import MediaAssetStatus
from app.infrastructure.models.media_asset import MediaAsset
from app.infrastructure.models.user import User
from app.infrastructure.providers.antivirus import MockAntivirusScanner
from app.main import app

DEV_EMAIL = "artist@example.com"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_mock_scanner_rejects_eicar():
    scanner = MockAntivirusScanner()
    clean = await scanner.scan(bucket="test", object_key="audio/track.wav")
    dirty = await scanner.scan(bucket="test", object_key="audio/eicar-test.bin")
    assert clean.clean is True
    assert dirty.clean is False
    assert dirty.threat_name == "EICAR-Test-File"


@pytest.mark.asyncio
async def test_complete_upload_scan_transition():
    async with SessionLocal() as db:
        user_result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        user = user_result.scalar_one_or_none()
        if user is None:
            pytest.skip("Seed user not in database")

        service = MediaService(scanner=MockAntivirusScanner())
        upload = await service.initiate_upload(
            db,
            user_id=user.id,
            filename="clean-track.wav",
            content_type="audio/wav",
            total_size=1024,
            ip_address=None,
        )

        await service.upload_part(
            db,
            user_id=user.id,
            upload_id=upload.id,
            part_number=1,
            body=b"fake-wav-data",
            ip_address=None,
        )

        asset = await service.complete_upload(
            db,
            user_id=user.id,
            upload_id=upload.id,
            parts=None,
            ip_address=None,
        )
        assert asset.status == MediaAssetStatus.READY

        result = await db.execute(select(MediaAsset).where(MediaAsset.id == asset.id))
        stored = result.scalar_one()
        assert stored.status == MediaAssetStatus.READY
        assert len(stored.versions) == 1


@pytest.mark.asyncio
async def test_list_upload_parts(client):
    login = await client.post("/api/v1/auth/dev-login", json={"email": DEV_EMAIL})
    if login.status_code == 404:
        pytest.skip("Seed user not in database")
    headers = {"Authorization": f"Bearer {login.json()['tokens']['access_token']}"}

    initiated = await client.post(
        "/api/v1/media/uploads/initiate",
        headers=headers,
        json={"filename": "resume.wav", "content_type": "audio/wav", "total_size": 2048},
    )
    assert initiated.status_code == 201
    upload_id = initiated.json()["upload_id"]

    parts = await client.get(f"/api/v1/media/uploads/{upload_id}/parts", headers=headers)
    assert parts.status_code == 200
    assert parts.json()["parts"] == []
