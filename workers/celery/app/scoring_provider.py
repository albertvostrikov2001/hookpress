"""LibROSA-based scoring provider (§11 advisory heuristics)."""

from abc import ABC, abstractmethod

import numpy as np

GENRE_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "pop": {"bpm": (90, 130), "loudness_lufs": (-14, -8), "spectral_centroid": (1500, 3500)},
    "rock": {"bpm": (100, 150), "loudness_lufs": (-12, -6), "spectral_centroid": (2000, 4500)},
    "hip-hop": {"bpm": (70, 110), "loudness_lufs": (-10, -6), "spectral_centroid": (1000, 3000)},
    "electronic": {"bpm": (120, 140), "loudness_lufs": (-10, -6), "spectral_centroid": (2500, 5000)},
    "default": {"bpm": (80, 140), "loudness_lufs": (-16, -6), "spectral_centroid": (1200, 4000)},
}


class ScoringProvider(ABC):
    @abstractmethod
    def score_audio(self, audio_path: str, *, genre: str | None = None) -> dict:
        raise NotImplementedError


def _estimate_key(chroma: np.ndarray) -> str:
    pitch_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    chroma_mean = np.mean(chroma, axis=1)
    idx = int(np.argmax(chroma_mean))
    return f"{pitch_names[idx % 12]} major"


def _in_range(value: float, low: float, high: float) -> bool:
    return low <= value <= high


class LibrosaHeuristicProvider(ScoringProvider):
    def score_audio(self, audio_path: str, *, genre: str | None = None) -> dict:
        import librosa

        genre_key = (genre or "default").lower()
        ranges = GENRE_RANGES.get(genre_key, GENRE_RANGES["default"])

        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=120)
        if len(y) == 0:
            y = np.zeros(sr * 5, dtype=np.float32)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo) if np.isscalar(tempo) else float(tempo[0])
        if bpm <= 0:
            bpm = float(librosa.feature.rhythm.tempo(y=y, sr=sr, aggregate=np.median)[0])
        if bpm <= 0:
            bpm = 120.0

        spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        rms = librosa.feature.rms(y=y)[0]
        dynamic_range_db = float(20 * np.log10(np.max(rms) / (np.min(rms[rms > 0]) + 1e-9)))

        loudness_lufs = float(-0.691 + 10 * np.log10(np.mean(rms**2) + 1e-12))

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        intro_duration_sec = (
            float(librosa.frames_to_time(onset_frames[0], sr=sr)) if len(onset_frames) else 0.0
        )

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key = _estimate_key(chroma)

        energy = float(np.clip(np.mean(rms) * 10, 0, 1))
        danceability = float(np.clip(bpm / 180, 0, 1))

        reasons: list[str] = []
        recommendations: list[str] = []
        score_parts: list[float] = []

        if _in_range(bpm, *ranges["bpm"]):
            reasons.append(f"BPM {bpm:.0f} fits {genre_key} range {ranges['bpm']}")
            score_parts.append(25)
        else:
            recommendations.append(
                f"Consider adjusting tempo toward {ranges['bpm'][0]}-{ranges['bpm'][1]} BPM for {genre_key}"
            )
            score_parts.append(10)

        if _in_range(spectral_centroid, *ranges["spectral_centroid"]):
            reasons.append("Spectral brightness aligns with genre expectations")
            score_parts.append(20)
        else:
            recommendations.append("EQ adjustments may improve genre fit")
            score_parts.append(8)

        if dynamic_range_db >= 6:
            reasons.append(f"Dynamic range {dynamic_range_db:.1f} dB provides adequate contrast")
            score_parts.append(20)
        else:
            recommendations.append("Increase dynamic range for more expressive delivery")
            score_parts.append(8)

        if intro_duration_sec <= 15:
            reasons.append(f"Intro length {intro_duration_sec:.1f}s is streaming-friendly")
            score_parts.append(15)
        else:
            recommendations.append("Long intro may reduce streaming retention")
            score_parts.append(5)

        advisory_score = float(min(100, sum(score_parts)))
        confidence = float(np.clip(len(y) / (sr * 30), 0.3, 0.95))

        limitations = [
            "Advisory heuristics only — not a hit prediction",
            "Analysis limited to first 120 seconds of audio",
            "Genre ranges are approximate benchmarks",
        ]

        return {
            "bpm": round(bpm, 1),
            "key": key,
            "spectral_centroid": round(spectral_centroid, 1),
            "dynamic_range_db": round(dynamic_range_db, 2),
            "intro_duration_sec": round(intro_duration_sec, 2),
            "loudness_lufs": round(loudness_lufs, 2),
            "energy": round(energy, 2),
            "danceability": round(danceability, 2),
            "genre": genre_key,
            "genre_ranges": {k: list(v) for k, v in ranges.items()},
            "advisory_score": round(advisory_score, 1),
            "confidence": round(confidence, 2),
            "reasons": reasons,
            "recommendations": recommendations,
            "limitations": limitations,
            "source": "librosa_heuristic",
        }


def generate_synthetic_wav(path: str, *, seed: int = 42, duration_sec: float = 30.0) -> str:
    """Generate a deterministic test WAV file when no media is available."""
    import soundfile as sf

    sr = 22050
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    freq = 220 + (seed % 200)
    y = 0.3 * np.sin(2 * np.pi * freq * t)
    y += 0.1 * np.sin(2 * np.pi * (freq * 1.5) * t)
    sf.write(path, y.astype(np.float32), sr)
    return path
