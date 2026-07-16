"""Studio Celery tasks."""

import io
import uuid
from datetime import UTC, datetime

import numpy as np
from sqlalchemy import func, select

from app.celery_app import celery_app
from app.db import AiTask, LyricVersion, StudioProject, get_session, publish_task_event
from app.providers import MockAudioProvider, MockLLMProvider
from app.state_machines import ai_task_state_machine
from app.storage import download_object_to_file, upload_bytes


def _set_task_status(session, task: AiTask, status: str, **fields) -> None:
    ai_task_state_machine.assert_transition(task.status, status)
    task.status = status
    for key, value in fields.items():
        setattr(task, key, value)
    session.flush()
    publish_task_event(
        str(task.id),
        {"event": "status", "status": status, "task_id": str(task.id), **fields},
    )


def _compute_peaks_from_bytes(data: bytes, *, num_peaks: int = 200) -> dict:
    try:
        import librosa

        y, sr = librosa.load(io.BytesIO(data), sr=22050, mono=True)
    except Exception:
        arr = np.frombuffer(data[: num_peaks * 4], dtype=np.uint8).astype(np.float32)
        if len(arr) == 0:
            arr = np.zeros(num_peaks, dtype=np.float32)
        chunk = max(1, len(arr) // num_peaks)
        peaks = [float(np.max(arr[i : i + chunk])) for i in range(0, len(arr), chunk)][:num_peaks]
        return {"peaks": peaks, "sample_rate": 22050, "duration_sec": len(arr) / 22050}

    chunk = max(1, len(y) // num_peaks)
    peaks = [float(np.max(np.abs(y[i : i + chunk]))) for i in range(0, len(y), chunk)][:num_peaks]
    max_peak = max(peaks) if peaks else 1.0
    normalized = [round(p / max_peak, 4) for p in peaks]
    return {
        "peaks": normalized,
        "sample_rate": sr,
        "duration_sec": round(len(y) / sr, 2),
    }


@celery_app.task(name="studio.generate_lyrics", bind=True)
def generate_lyrics_task(self, ai_task_id: str, prompt: str | None = None):
    llm = MockLLMProvider()
    task_uuid = uuid.UUID(ai_task_id)

    with get_session() as session:
        task = session.get(AiTask, task_uuid)
        if task is None:
            return {"error": "task_not_found"}

        prompt_text = prompt or (task.input_payload or {}).get("prompt", "")
        _set_task_status(session, task, "PROCESSING")

        try:
            lyrics = llm.generate_lyrics(prompt_text)
            version_number = session.execute(
                select(func.coalesce(func.max(LyricVersion.version_number), 0)).where(
                    LyricVersion.studio_project_id == task.studio_project_id
                )
            ).scalar_one()
            version = LyricVersion(
                id=uuid.uuid4(),
                studio_project_id=task.studio_project_id,
                version_number=version_number + 1,
                content=lyrics,
                prompt=prompt_text,
                ai_task_id=task.id,
            )
            session.add(version)

            result = {"lyric_version_id": str(version.id), "content_preview": lyrics[:200]}
            task.result_payload = result
            task.completed_at = datetime.now(UTC)
            _set_task_status(session, task, "SUCCEEDED", result_payload=result)
            return result
        except Exception as exc:
            task.error_message = str(exc)
            task.completed_at = datetime.now(UTC)
            _set_task_status(session, task, "FAILED", error_message=str(exc))
            raise


@celery_app.task(name="studio.generate_audio", bind=True)
def generate_audio_task(
    self,
    ai_task_id: str,
    lyrics: str | None = None,
    lyric_version_id: str | None = None,
):
    audio = MockAudioProvider()
    task_uuid = uuid.UUID(ai_task_id)

    with get_session() as session:
        task = session.get(AiTask, task_uuid)
        if task is None:
            return {"error": "task_not_found"}

        lyrics_text = lyrics or (task.input_payload or {}).get("lyrics", "")
        _set_task_status(session, task, "PROCESSING")

        try:
            publish_task_event(
                str(task.id),
                {"event": "progress", "status": "PROCESSING", "progress": 50},
            )
            demo_bytes = audio.generate_demo(lyrics_text)

            project = session.get(StudioProject, task.studio_project_id)
            media_asset_id = None
            if project:
                asset = upload_bytes(
                    user_id=project.user_id,
                    data=demo_bytes,
                    content_type="audio/mpeg",
                    suffix=".mp3",
                )
                session.add(asset)
                session.flush()
                media_asset_id = str(asset.id)

            result = {
                "size_bytes": len(demo_bytes),
                "lyric_version_id": lyric_version_id
                or (task.input_payload or {}).get("lyric_version_id"),
                "format": "mock-mp3",
                "media_asset_id": media_asset_id,
            }
            peaks_data = _compute_peaks_from_bytes(demo_bytes)
            task.result_metadata = peaks_data
            task.result_payload = result
            task.completed_at = datetime.now(UTC)
            _set_task_status(
                session,
                task,
                "SUCCEEDED",
                result_payload=result,
                result_metadata=peaks_data,
            )
            return result
        except Exception as exc:
            task.error_message = str(exc)
            task.completed_at = datetime.now(UTC)
            _set_task_status(session, task, "FAILED", error_message=str(exc))
            raise


@celery_app.task(name="studio.generate_waveform", bind=True)
def generate_waveform_task(self, ai_task_id: str, source_audio_task_id: str | None = None):
    task_uuid = uuid.UUID(ai_task_id)
    source_id = uuid.UUID(source_audio_task_id) if source_audio_task_id else task_uuid

    with get_session() as session:
        task = session.get(AiTask, task_uuid)
        if task is None:
            return {"error": "task_not_found"}

        source = session.get(AiTask, source_id)
        if source is None or not source.result_payload:
            task.error_message = "source audio task not found"
            task.completed_at = datetime.now(UTC)
            _set_task_status(session, task, "FAILED", error_message=task.error_message)
            return {"error": "source_not_found"}

        _set_task_status(session, task, "PROCESSING")

        try:
            audio_bytes = b""
            asset_id_str = source.result_payload.get("media_asset_id")
            if asset_id_str:
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
                    download_object_to_file(uuid.UUID(asset_id_str), tmp.name, session=session)
                    with open(tmp.name, "rb") as f:
                        audio_bytes = f.read()
            else:
                audio_bytes = b"\x00" * 4096

            peaks_data = _compute_peaks_from_bytes(audio_bytes)
            task.result_metadata = peaks_data
            task.result_payload = {"source_audio_task_id": str(source_id), "peak_count": len(peaks_data["peaks"])}
            task.completed_at = datetime.now(UTC)
            _set_task_status(
                session,
                task,
                "SUCCEEDED",
                result_payload=task.result_payload,
                result_metadata=peaks_data,
            )
            return {"result_metadata": peaks_data}
        except Exception as exc:
            task.error_message = str(exc)
            task.completed_at = datetime.now(UTC)
            _set_task_status(session, task, "FAILED", error_message=str(exc))
            raise
