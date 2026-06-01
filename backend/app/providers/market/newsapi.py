from __future__ import annotations

from datetime import datetime

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import BaseMarketProvider, NewsArticle

_BASE = "https://newsapi.org/v2"


class NewsAPIProvider(BaseMarketProvider):
    name = "newsapi"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, path: str, params: dict) -> dict:
        params = {**params, "apiKey": self._key}
        try:
            resp = await self._client.get(f"{_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"newsapi {path} error: {exc}") from exc

    async def get_news(self, symbol: str | None, category: str, limit: int) -> list[NewsArticle]:
        if symbol is None:
            data = await self._get(
                "/top-headlines", {"category": "business", "language": "en", "pageSize": limit}
            )
            resolved_category = "macro"
        else:
            data = await self._get(
                "/everything",
                {"q": symbol.upper(), "language": "en", "sortBy": "publishedAt", "pageSize": limit},
            )
            resolved_category = category
        if data.get("status") != "ok":
            raise ProviderError(f"newsapi: {data.get('message', 'error')}")
        articles: list[NewsArticle] = []
        for item in data.get("articles", [])[:limit]:
            published = item.get("publishedAt")
            articles.append(
                NewsArticle(
                    headline=item.get("title") or "",
                    summary=item.get("description"),
                    url=item.get("url") or "",
                    source=(item.get("source") or {}).get("name"),
                    published_at=_parse_dt(published),
                    category=resolved_category,
                )
            )
        return [a for a in articles if a.headline and a.url]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
