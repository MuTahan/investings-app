"""xAI (Grok) chat client — OpenAI-compatible /chat/completions.

Powers the conversational "discuss this stock" assistant. Separate from the
committee's LLMProvider (which is single-shot JSON) because chat is multi-turn.
"""

from __future__ import annotations

import httpx

from app.core.exceptions import ProviderError


class XaiChat:
    name = "xai"

    def __init__(
        self, client: httpx.AsyncClient, api_key: str, base_url: str, model: str
    ) -> None:
        self._client = client
        self._key = api_key
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._model = model

    async def chat(self, messages: list[dict], *, max_tokens: int = 800) -> str:
        headers = {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}
        body = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            resp = await self._client.post(self._url, headers=headers, json=body, timeout=45.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"xai chat error: {exc}") from exc
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("xai: malformed chat response") from exc
