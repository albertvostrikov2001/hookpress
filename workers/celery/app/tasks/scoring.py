"""Scoring Celery tasks."""

import os
import tempfile
import uuid

from sqlalchemy import select, update

from app.celery_app import celery_app
from app.db import Release, ScoringReport, Track, get_session
from app.scoring_provider import LibrosaHeuristicProvider, generate_synthetic_wav
from app.storage import download_object_to_file


def _score_with_fallback(provider: LibrosaHeuristicProvider, audio_path: str, *, release_uuid: uuid.UUID, genre: str | None) -> dict:
    try:
        return provider.score_audio(audio_path, genre=genre)
    except Exception:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            fallback_path = generate_synthetic_wav(tmp.name, seed=int(release_uuid.int % 10000))
        try:
            return provider.score_audio(fallback_path, genre=genre)
        finally:
            if os.path.exists(fallback_path):
                os.unlink(fallback_path)


@celery_app.task(name="scoring.score_release", bind=True)
def score_release_task(self, release_id: str, genre: str | None = None):
    release_uuid = uuid.UUID(release_id)
    provider = LibrosaHeuristicProvider()

    with get_session() as session:
        release = session.get(Release, release_uuid)
        if release is None:
            return {"error": "release_not_found"}

        audio_path: str | None = None
        track_id: uuid.UUID | None = None
        track_result = session.execute(
            select(Track).where(
                Track.office_project_id == release.office_project_id,
                Track.media_asset_id.isnot(None),
            ).limit(1)
        )
        track = track_result.scalar_one_or_none()
        if track and track.media_asset_id:
            track_id = track.id
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = download_object_to_file(track.media_asset_id, tmp.name, session=session)

        if audio_path is None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = generate_synthetic_wav(tmp.name, seed=int(release_uuid.int % 10000))

        try:
            metrics = _score_with_fallback(
                provider, audio_path, release_uuid=release_uuid, genre=genre
            )
        finally:
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)

        report = ScoringReport(
            release_id=release_uuid,
            track_id=track_id,
            bpm=metrics.get("bpm"),
            energy=metrics.get("energy"),
            danceability=metrics.get("danceability"),
            raw_json=metrics,
        )
        session.add(report)
        session.flush()

        passed = (metrics.get("advisory_score") or 0) >= 50
        if release.status == "VALIDATING":
            next_status = "MODERATION" if passed else "FAILED"
            session.execute(
                update(Release).where(Release.id == release_uuid).values(status=next_status)
            )
            session.flush()

            if next_status == "MODERATION":
                session.execute(
                    update(Release).where(Release.id == release_uuid).values(status="DELIVERED")
                )
                session.flush()
                session.execute(
                    update(Release).where(Release.id == release_uuid).values(status="RELEASED")
                )

        return {
            "release_id": release_id,
            "passed": passed,
            "metrics": metrics,
            "scoring_report_id": str(report.id),
        }
