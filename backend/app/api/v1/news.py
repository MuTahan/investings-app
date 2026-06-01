from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentUserDep, ProvidersDep, SessionDep
from app.schemas.news import NewsListResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
async def list_news(
    session: SessionDep,
    providers: ProvidersDep,
    _: CurrentUserDep,
    symbol: str | None = Query(default=None),
    category: str = Query(default="company"),
    limit: int = Query(default=20, ge=1, le=50),
) -> NewsListResponse:
    items = await NewsService(session, providers.market).list(symbol, category, limit)
    return NewsListResponse(items=items)
