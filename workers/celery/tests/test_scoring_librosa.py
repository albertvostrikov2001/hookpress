"""LibROSA worker scoring tests."""

import math
import struct
import tempfile
import wave

import pytest

librosa = pytest.importorskip("librosa")

from app.scoring_provider import LibrosaHeuristicProvider, generate_synthetic_wav


def _write_test_wav(path: str, *, freq: float = 440.0, duration: float = 2.0, sr: int = 22050) -> None:
    n_samples = int(sr * duration)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(n_samples):
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sr))
            wf.writeframes(struct.pack("<h", sample))


def test_librosa_heuristic_scores_synthetic_wav():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        _write_test_wav(tmp.name, freq=120.0, duration=3.0)
        provider = LibrosaHeuristicProvider()
        result = provider.score_audio(tmp.name, genre="pop")

    assert result["source"] == "librosa_heuristic"
    assert result["bpm"] > 0
    assert result["key"]
    assert result["spectral_centroid"] > 0
    assert "advisory_score" in result
    assert result["confidence"] > 0
    assert isinstance(result["reasons"], list)
    assert isinstance(result["recommendations"], list)
    assert isinstance(result["limitations"], list)
    assert "bpm" in result["genre_ranges"]


def test_generate_synthetic_wav():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        generate_synthetic_wav(tmp.name, seed=7)
        provider = LibrosaHeuristicProvider()
        result = provider.score_audio(tmp.name, genre="electronic")
    assert result["genre"] == "electronic"
