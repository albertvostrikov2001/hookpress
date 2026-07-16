"""Provider factory."""

import os

from app.infrastructure.providers.base import (
    AudioProvider,
    LLMProvider,
    MockAudioProvider,
    MockLLMProvider,
)
from app.infrastructure.providers.llm import ClaudeLLMProvider, OpenAILLMProvider, YandexGPTLLMProvider
from app.infrastructure.providers.payment import MockPaymentProvider, PaymentProvider
from app.infrastructure.providers.scoring import (
    LibrosaHeuristicProvider,
    MockScoringProvider,
    ScoringProvider,
)

_payment_provider: MockPaymentProvider | None = None


def get_llm_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        return MockLLMProvider()
    if provider == "openai":
        return OpenAILLMProvider()
    if provider == "claude":
        return ClaudeLLMProvider()
    if provider == "yandex":
        return YandexGPTLLMProvider()
    raise NotImplementedError(f"LLM provider '{provider}' not configured")


def get_audio_provider() -> AudioProvider:
    provider = os.getenv("AUDIO_PROVIDER", "mock")
    if provider == "mock":
        return MockAudioProvider()
    raise NotImplementedError(f"Audio provider '{provider}' not configured in MVP")


def get_payment_provider() -> PaymentProvider:
    global _payment_provider
    provider = os.getenv("PAYMENT_PROVIDER", "mock")
    if provider == "mock":
        if _payment_provider is None:
            _payment_provider = MockPaymentProvider()
        return _payment_provider
    raise NotImplementedError(f"Payment provider '{provider}' not configured in MVP")


def get_scoring_provider() -> ScoringProvider:
    provider = os.getenv("SCORING_PROVIDER", "librosa").lower()
    if provider in {"librosa", "mock"}:
        if provider == "mock":
            return MockScoringProvider()
        return LibrosaHeuristicProvider()
    raise NotImplementedError(f"Scoring provider '{provider}' not configured")
