from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentUserDep, ProvidersDep, SessionDep, SettingsDep
from app.schemas.news import NewsImpactReport, NewsListResponse
from app.services.news_service import NewsService
from app.services.news_workflow_service import NewsWorkflowService

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


@router.get("/impact", response_model=NewsImpactReport)
async def news_impact(
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    symbol: str = Query(min_length=1, max_length=20),
) -> NewsImpactReport:
    return await NewsWorkflowService(session, providers, settings).analyze(user, symbol)
