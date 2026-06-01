from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import NewsCategory


class NewsItemOut(BaseModel):
    headline: str
    summary: str | None = None
    url: str
    source: str | None = None
    published_at: datetime | None = None
    sentiment: float | None = None
    category: NewsCategory = NewsCategory.COMPANY


class NewsListResponse(BaseModel):
    items: list[NewsItemOut]
