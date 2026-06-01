"""Deterministic stub LLM used when no AI key is configured (and in tests).

Lets the system run end-to-end without external AI calls. Phase 4 agents detect this
provider and fall back to their deterministic anchors with templated explanations.
"""

from __future__ import annotations

from typing import Any


class StubLLMProvider:
    name = "stub"

    async def complete_text(self, prompt: str, *, model: str, max_tokens: int = 600) -> str:
        return "Explanation unavailable (AI provider not configured)."

    async def complete_json(
        self, prompt: str, *, model: str, max_tokens: int = 800
    ) -> dict[str, Any]:
        # Empty object -> callers treat as "no adjustment" and keep the deterministic anchor.
        return {}
