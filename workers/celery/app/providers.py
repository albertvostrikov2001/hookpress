"""Mock providers for Celery workers."""


class MockLLMProvider:
    def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        return f"[mock lyrics for: {prompt[:80]}]\n\nVerse 1...\nChorus..."


class MockAudioProvider:
    def generate_demo(self, lyrics: str, **kwargs: object) -> bytes:
        return b"ID3mock" + lyrics[:32].encode("utf-8", errors="ignore")
