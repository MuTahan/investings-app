"""Recommendations endpoints — the AI Investment Committee (Phase 4)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CurrentUserDep, ProvidersDep, SessionDep, SettingsDep
from app.schemas.recommendation import (
    RecommendationCenterResponse,
    RecommendationListResponse,
    RecommendationOut,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _service(session: SessionDep, providers: ProvidersDep, settings: SettingsDep):
    return RecommendationService(session, providers, settings)


@router.get("", response_model=RecommendationListResponse)
async def list_recommendations(
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    scope: str = Query(default="watchlist", pattern="^(watchlist|portfolio)$"),
) -> RecommendationListResponse:
    items = await _service(session, providers, settings).list_scope(user, scope)
    return RecommendationListResponse(items=items)


@router.get("/center", response_model=RecommendationCenterResponse)
async def recommendation_center(
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    horizon: str | None = Query(default=None),
    risk: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    type: str | None = Query(default=None),
    min_confidence: float = Query(default=0.0, ge=0, le=100),
) -> RecommendationCenterResponse:
    return await _service(session, providers, settings).center(
        user,
        horizon=horizon,
        risk=risk,
        sector=sector,
        rec_type=type,
        min_confidence=min_confidence,
    )


@router.get("/{symbol}", response_model=RecommendationOut)
async def get_recommendation(
    symbol: str,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    refresh: bool = Query(default=False),
) -> RecommendationOut:
    return await _service(session, providers, settings).get(user, symbol, refresh)


@router.get("/{symbol}/history", response_model=RecommendationListResponse)
async def recommendation_history(
    symbol: str,
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationListResponse:
    items = await _service(session, providers, settings).history(user, symbol, limit)
    return RecommendationListResponse(items=items)
