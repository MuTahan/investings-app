from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query

from app.deps import CurrentUserDep, ProvidersDep, SessionDep
from app.schemas.market import (
    CandleSeriesOut,
    InstrumentOut,
    QuoteOut,
    SearchResponse,
)
from app.schemas.trending import TrendingResponse
from app.services.market_service import MarketService
from app.services.trending_service import TrendingService

router = APIRouter(prefix="/market", tags=["market"])

_VALID_RESOLUTIONS = {"1", "5", "15", "60", "D", "W"}


def _service(session: SessionDep, providers: ProvidersDep) -> MarketService:
    return MarketService(session, providers.market)


@router.get("/trending", response_model=TrendingResponse)
async def trending(
    session: SessionDep,
    providers: ProvidersDep,
    _: CurrentUserDep,
    category: str = Query(default="trending"),
    limit: int = Query(default=12, ge=1, le=50),
) -> TrendingResponse:
    items = await TrendingService(session, providers).get(category, limit)
    return TrendingResponse(category=category, items=items)


@router.get("/search", response_model=SearchResponse)
async def search(
    session: SessionDep,
    providers: ProvidersDep,
    _: CurrentUserDep,
    q: str = Query(min_length=1, max_length=40),
    limit: int = Query(default=20, ge=1, le=100),
) -> SearchResponse:
    results = await _service(session, providers).search(q, limit)
    return SearchResponse(results=results)


@router.get("/instruments/{symbol}", response_model=InstrumentOut)
async def get_instrument(
    symbol: str, session: SessionDep, providers: ProvidersDep, _: CurrentUserDep
) -> InstrumentOut:
    return await _service(session, providers).get_instrument(symbol)


@router.get("/quote/{symbol}", response_model=QuoteOut)
async def get_quote(
    symbol: str, session: SessionDep, providers: ProvidersDep, _: CurrentUserDep
) -> QuoteOut:
    return await _service(session, providers).get_quote(symbol)


@router.get("/candles/{symbol}", response_model=CandleSeriesOut)
async def get_candles(
    symbol: str,
    session: SessionDep,
    providers: ProvidersDep,
    _: CurrentUserDep,
    resolution: str = Query(default="D"),
    days: int = Query(default=180, ge=1, le=4000),
) -> CandleSeriesOut:
    resolution = resolution if resolution in _VALID_RESOLUTIONS else "D"
    to = datetime.now(UTC)
    frm = to - timedelta(days=days)
    return await _service(session, providers).get_candles(symbol, resolution, frm, to)
