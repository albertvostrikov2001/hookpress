"""LibROSA scoring provider tests (API layer)."""

import pytest

from app.infrastructure.providers.factory import get_scoring_provider
from app.infrastructure.providers.scoring import LibrosaHeuristicProvider, MockScoringProvider


def test_mock_scoring_provider():
    provider = MockScoringProvider()
    result = provider.score_audio("/tmp/mock.wav", genre="pop")
    assert result["source"] == "mock"
    assert result["advisory_score"] == 72.0
    assert "limitations" in result
    assert "genre_ranges" in result


def test_api_librosa_provider_delegates():
    provider = LibrosaHeuristicProvider()
    result = provider.score_audio("/tmp/unused.wav", genre="rock")
    assert result["source"] == "api_delegated"
    assert "reasons" in result
    assert result["confidence"] == 0.0


def test_factory_default_scoring_provider():
    provider = get_scoring_provider()
    assert isinstance(provider, LibrosaHeuristicProvider)


def test_factory_mock_scoring_provider(monkeypatch):
    monkeypatch.setenv("SCORING_PROVIDER", "mock")
    provider = get_scoring_provider()
    assert isinstance(provider, MockScoringProvider)
