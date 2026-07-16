"""Provider factory tests."""

import pytest

from app.infrastructure.providers.factory import get_audio_provider, get_llm_provider, get_scoring_provider
from app.infrastructure.providers.scoring import LibrosaHeuristicProvider, MockScoringProvider


@pytest.mark.asyncio
async def test_mock_llm_provider():
    provider = get_llm_provider()
    result = await provider.generate_lyrics("test theme")
    assert "[mock lyrics" in result


@pytest.mark.asyncio
async def test_mock_audio_provider():
    provider = get_audio_provider()
    result = await provider.generate_demo("lyrics")
    assert result.startswith(b"ID3")


def test_scoring_provider_factory_default():
    provider = get_scoring_provider()
    assert isinstance(provider, LibrosaHeuristicProvider)


def test_scoring_provider_factory_mock(monkeypatch):
    monkeypatch.setenv("SCORING_PROVIDER", "mock")
    provider = get_scoring_provider()
    assert isinstance(provider, MockScoringProvider)
