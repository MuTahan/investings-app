from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    market,
    news,
    notifications,
    portfolio,
    recommendations,
    system,
    user,
    watchlist,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(market.router)
api_router.include_router(watchlist.router)
api_router.include_router(portfolio.router)
api_router.include_router(news.router)
api_router.include_router(recommendations.router)
api_router.include_router(notifications.router)
