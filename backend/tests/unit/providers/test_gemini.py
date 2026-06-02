from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import ProviderError
from app.providers.llm.gemini_provider import GeminiProvider


class FakeClient:
    """Minimal async client double that returns a canned Gemini response."""

    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.calls: list[dict] = []

    async def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return httpx.Response(
            self.status, json=self.payload, request=httpx.Request("POST", url)
        )


def _reply(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


async def test_complete_text_returns_joined_parts():
    client = FakeClient(_reply("Apple looks strong."))
    provider = GeminiProvider(client, "KEY")  # type: ignore[arg-type]

    out = await provider.complete_text("Analyze AAPL", model="gemini-2.5-flash")

    assert out == "Apple looks strong."
    call = client.calls[0]
    assert call["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert call["headers"]["x-goog-api-key"] == "KEY"  # key in header, not URL
    assert "key=" not in call["url"]


async def test_complete_json_parses_object_and_sets_json_mode():
    client = FakeClient(_reply('{"rating": "BUY", "score": 7}'))
    provider = GeminiProvider(client, "KEY")  # type: ignore[arg-type]

    out = await provider.complete_json("Rate AAPL", model="gemini-2.5-flash")

    assert out == {"rating": "BUY", "score": 7}
    cfg = client.calls[0]["json"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json"


async def test_complete_json_tolerates_surrounding_prose():
    client = FakeClient(_reply('Here you go:\n{"ok": true}\nThanks!'))
    provider = GeminiProvider(client, "KEY")  # type: ignore[arg-type]

    out = await provider.complete_json("x", model="gemini-2.5-flash")

    assert out == {"ok": True}


async def test_empty_candidates_raises_provider_error():
    client = FakeClient({"candidates": []})
    provider = GeminiProvider(client, "KEY")  # type: ignore[arg-type]

    with pytest.raises(ProviderError):
        await provider.complete_text("x", model="gemini-2.5-flash")
