"""Scoring provider interface (§11 advisory heuristics)."""

from abc import ABC, abstractmethod


class ScoringProvider(ABC):
    @abstractmethod
    def score_audio(self, audio_path: str, *, genre: str | None = None) -> dict:
        raise NotImplementedError


class LibrosaHeuristicProvider(ScoringProvider):
    """API-side stub; real LibROSA analysis runs in Celery worker."""

    def score_audio(self, audio_path: str, *, genre: str | None = None) -> dict:
        return {
            "bpm": None,
            "key": None,
            "spectral_centroid": None,
            "dynamic_range_db": None,
            "intro_duration_sec": None,
            "loudness_lufs": None,
            "genre": genre,
            "genre_ranges": {},
            "advisory_score": None,
            "confidence": 0.0,
            "reasons": ["Scoring runs asynchronously in Celery worker"],
            "recommendations": [],
            "limitations": ["Use POST /office/releases/{id}/submit to trigger LibROSA scoring"],
            "source": "api_delegated",
            "audio_path": audio_path,
        }


class MockScoringProvider(ScoringProvider):
    def score_audio(self, audio_path: str, *, genre: str | None = None) -> dict:
        return {
            "bpm": 120.0,
            "key": "C major",
            "spectral_centroid": 2000.0,
            "dynamic_range_db": 8.0,
            "intro_duration_sec": 8.0,
            "loudness_lufs": -10.0,
            "genre": genre or "pop",
            "genre_ranges": {"bpm": [100, 130]},
            "advisory_score": 72.0,
            "confidence": 0.5,
            "reasons": ["Mock scoring — no audio analysis performed"],
            "recommendations": ["Upload a mastered track for real heuristics"],
            "limitations": ["Advisory only; not a hit prediction"],
            "source": "mock",
            "audio_path": audio_path,
        }
