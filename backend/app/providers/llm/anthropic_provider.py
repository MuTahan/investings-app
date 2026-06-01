from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.exceptions import ProviderError

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _message(self, prompt: str, model: str, max_tokens: int) -> str:
        headers = {
            "x-api-key": self._key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            resp = await self._client.post(_URL, headers=headers, json=body, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"anthropic error: {exc}") from exc
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    async def complete_text(self, prompt: str, *, model: str, max_tokens: int = 600) -> str:
        return await self._message(prompt, model, max_tokens)

    async def complete_json(
        self, prompt: str, *, model: str, max_tokens: int = 800
    ) -> dict[str, Any]:
        text = await self._message(
            prompt + "\n\nRespond with ONLY a valid JSON object, no prose.", model, max_tokens
        )
        return _extract_json(text)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ProviderError("anthropic: no JSON in response")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ProviderError(f"anthropic: invalid JSON: {exc}") from exc
