"""External provider interfaces (stubs)."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        return f"[mock lyrics for: {prompt[:80]}]"


class AudioProvider(ABC):
    @abstractmethod
    async def generate_demo(self, lyrics: str, **kwargs: object) -> bytes:
        raise NotImplementedError


class MockAudioProvider(AudioProvider):
    async def generate_demo(self, lyrics: str, **kwargs: object) -> bytes:
        return b"ID3mock"
