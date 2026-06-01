from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.exceptions import ProviderError

_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider:
    name = "openai"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _chat(self, prompt: str, model: str, max_tokens: int, json_mode: bool) -> str:
        headers = {"Authorization": f"Bearer {self._key}", "content-type": "application/json"}
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            resp = await self._client.post(_URL, headers=headers, json=body, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"openai error: {exc}") from exc
        return data["choices"][0]["message"]["content"]

    async def complete_text(self, prompt: str, *, model: str, max_tokens: int = 600) -> str:
        return await self._chat(prompt, model, max_tokens, json_mode=False)

    async def complete_json(
        self, prompt: str, *, model: str, max_tokens: int = 800
    ) -> dict[str, Any]:
        text = await self._chat(prompt, model, max_tokens, json_mode=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"openai: invalid JSON: {exc}") from exc
