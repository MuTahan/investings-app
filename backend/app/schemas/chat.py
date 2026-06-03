from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    symbol: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list, max_length=30)


class ChatResponse(BaseModel):
    reply: str
