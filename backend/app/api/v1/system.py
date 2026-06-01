from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.deps import ProvidersDep, SessionDep, SettingsDep

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(session: SessionDep, providers: ProvidersDep, settings: SettingsDep) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "llm": providers.llm.name,
        "decision_mode": settings.ai_decision_mode,
        "market_vendors": providers.market_vendors,
        "notification_channels": providers.notifier.channels,
        "scheduler_enabled": settings.scheduler_enabled,
        "environment": settings.environment,
    }
