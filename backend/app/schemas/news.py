from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import NewsCategory, Recommendation


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


class NewsImpactItem(BaseModel):
    headline: str
    url: str
    source: str | None = None
    published_at: datetime | None = None
    impact_score: int
    impact_label: str


class NewsImpactReport(BaseModel):
    symbol: str
    article_count: int
    net_sentiment: float
    sentiment_label: str
    predicted_short_term: str
    predicted_long_term: str
    recommended_action: Recommendation | None = None
    confidence: float | None = None
    summary: str
    items: list[NewsImpactItem]
