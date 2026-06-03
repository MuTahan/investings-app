"""Google Gemini (Generative Language API) LLM provider.

Implements the same LLMProvider protocol as the Anthropic/OpenAI adapters, so the
Investment Committee can run "empowered" on a Google AI Studio key. Uses the
v1beta `generateContent` REST endpoint with the API key in the `x-goog-api-key`
header (keeps the secret out of the URL/logs) and Gemini's native JSON mode via
`generationConfig.responseMimeType`.

The committee fans out ~7 calls (6 agents + chair) at once, which easily trips a
free/standard-tier rate limit. To survive that (a locked architecture decision),
this provider caps in-flight requests with a semaphore and retries 429/500/503
with exponential backoff, honouring Gemini's `RetryInfo.retryDelay` when present.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx

from app.core.exceptions import ProviderError

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_MAX_CONCURRENCY = 2  # cap simultaneous calls so the committee fan-out doesn't burst
_MAX_ATTEMPTS = 3  # for transient 500/503 only
_RETRYABLE_SERVER = {500, 503}
_MAX_BACKOFF_SECONDS = 4.0
# After a 429 we stop calling Gemini for this long so the committee falls back to
# deterministic *instantly* instead of stalling on retries for every stock. When the
# quota frees up the next call after the window simply succeeds.
_COOLDOWN_SECONDS = 90.0


class GeminiProvider:
    name = "google"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key
        self._sem: asyncio.Semaphore | None = None
        self._cooldown_until = 0.0  # monotonic deadline; >now means circuit open

    def _semaphore(self) -> asyncio.Semaphore:
        # Lazily created inside the running loop; safe because there is no await
        # between the check and the assignment (asyncio is single-threaded).
        if self._sem is None:
            self._sem = asyncio.Semaphore(_MAX_CONCURRENCY)
        return self._sem

    async def _generate(
        self, prompt: str, model: str, max_tokens: int, *, json_mode: bool
    ) -> str:
        headers = {"x-goog-api-key": self._key, "content-type": "application/json"}
        generation_config: dict[str, Any] = {"maxOutputTokens": max_tokens}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        # Gemini 2.5/3.x are reasoning models that spend output budget on hidden
        # "thinking" tokens, which can starve the visible response under our token
        # cap. The committee wants concise verdicts, not extended reasoning, so we
        # turn thinking off for those families (faster + cheaper + non-empty output).
        if any(tag in model for tag in ("2.5", "gemini-3", "3.1", "3.5")):
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        url = f"{_BASE}/{model}:generateContent"

        # Circuit breaker: if a recent call was rate-limited, skip the network entirely
        # so the caller falls back to its deterministic anchor without delay.
        if time.monotonic() < self._cooldown_until:
            raise ProviderError("gemini: rate-limited (cooling down)")

        for attempt in range(_MAX_ATTEMPTS):
            try:
                async with self._semaphore():
                    resp = await self._client.post(url, headers=headers, json=body, timeout=30.0)
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    # Quota/rate limit — trip the breaker and fail fast (don't retry).
                    self._cooldown_until = time.monotonic() + _COOLDOWN_SECONDS
                    raise ProviderError("gemini: rate limited (429)") from exc
                if status in _RETRYABLE_SERVER and attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(min(1.5 * (attempt + 1), _MAX_BACKOFF_SECONDS))
                    continue
                raise ProviderError(f"gemini error: {exc}") from exc
            except httpx.HTTPError as exc:
                raise ProviderError(f"gemini error: {exc}") from exc

            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                raise ProviderError("gemini: empty response (no candidates)")
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts if "text" in p)

        raise ProviderError("gemini error: transient failures exhausted")

    async def complete_text(self, prompt: str, *, model: str, max_tokens: int = 600) -> str:
        return await self._generate(prompt, model, max_tokens, json_mode=False)

    async def complete_json(
        self, prompt: str, *, model: str, max_tokens: int = 800
    ) -> dict[str, Any]:
        text = await self._generate(prompt, model, max_tokens, json_mode=True)
        return _extract_json(text)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ProviderError("gemini: no JSON in response")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ProviderError(f"gemini: invalid JSON: {exc}") from exc
