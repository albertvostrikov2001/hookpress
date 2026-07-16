"""External LLM provider implementations."""

import os

import httpx

from app.infrastructure.providers.base import LLMProvider, MockLLMProvider


class OpenAILLMProvider(LLMProvider):
    def __init__(self) -> None:
        self._api_key = os.getenv("OPENAI_API_KEY", "")
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        if not self._api_key:
            return await MockLLMProvider().generate_lyrics(prompt, **kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a songwriting assistant. Write creative song lyrics.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def chat(self, messages: list[dict[str, str]]) -> str:
        if not self._api_key:
            last = messages[-1]["content"] if messages else ""
            return f"[mock assistant reply to: {last[:80]}]"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "messages": messages},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class ClaudeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        reply = await self.chat(
            [
                {
                    "role": "user",
                    "content": f"Write song lyrics for this theme:\n{prompt}",
                }
            ]
        )
        return reply

    async def chat(self, messages: list[dict[str, str]]) -> str:
        if not self._api_key:
            last = messages[-1]["content"] if messages else ""
            return f"[mock assistant reply to: {last[:80]}]"

        system = "You are a songwriting assistant for hook.press studio."
        user_messages = [m for m in messages if m["role"] == "user"]
        prompt = user_messages[-1]["content"] if user_messages else ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


class YandexGPTLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self._api_key = os.getenv("YANDEX_GPT_API_KEY", "")
        self._folder_id = os.getenv("YANDEX_FOLDER_ID", "")
        self._model = os.getenv("YANDEX_GPT_MODEL", "yandexgpt-lite")

    async def generate_lyrics(self, prompt: str, **kwargs: object) -> str:
        return await self.chat([{"role": "user", "content": f"Напиши текст песни: {prompt}"}])

    async def chat(self, messages: list[dict[str, str]]) -> str:
        if not self._api_key or not self._folder_id:
            last = messages[-1]["content"] if messages else ""
            return f"[mock assistant reply to: {last[:80]}]"

        model_uri = f"gpt://{self._folder_id}/{self._model}/latest"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers={"Authorization": f"Api-Key {self._api_key}"},
                json={
                    "modelUri": model_uri,
                    "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 1024},
                    "messages": [
                        {"role": m["role"].upper(), "text": m["content"]} for m in messages
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]["alternatives"][0]["message"]["text"]
