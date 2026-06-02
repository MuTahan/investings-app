from __future__ import annotations

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.deps import CurrentUserDep, ProvidersDep, SessionDep, SettingsDep
from app.repositories.device_repo import DeviceRepository
from app.repositories.notification_repo import NotificationPreferenceRepository
from app.schemas.common import Message
from app.schemas.notification import (
    NotificationFeedResponse,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    RunResult,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class RegisterDeviceRequest(BaseModel):
    device_token: str = Field(min_length=1, max_length=400)
    platform: str = "ios"


def _pref_out(pref) -> NotificationPreferenceOut:
    return NotificationPreferenceOut(
        categories=pref.categories or [],
        min_priority=pref.min_priority,
        max_risk=pref.max_risk,
        sectors=pref.sectors or [],
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
    )


@router.get("/preferences", response_model=NotificationPreferenceOut)
async def get_preferences(user: CurrentUserDep, session: SessionDep) -> NotificationPreferenceOut:
    pref = await NotificationPreferenceRepository(session).get_or_create(user.id)
    return _pref_out(pref)


@router.put("/preferences", response_model=NotificationPreferenceOut)
async def update_preferences(
    req: NotificationPreferenceUpdate, user: CurrentUserDep, session: SessionDep
) -> NotificationPreferenceOut:
    pref = await NotificationPreferenceRepository(session).upsert(
        user.id,
        categories=req.categories,
        min_priority=req.min_priority.value,
        max_risk=req.max_risk.value,
        sectors=req.sectors,
        quiet_hours_start=req.quiet_hours_start,
        quiet_hours_end=req.quiet_hours_end,
    )
    return _pref_out(pref)


@router.get("", response_model=NotificationFeedResponse)
async def list_notifications(
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
    limit: int = Query(default=50, ge=1, le=100),
) -> NotificationFeedResponse:
    items = await NotificationService(session, providers, settings).list_feed(user, limit)
    return NotificationFeedResponse(items=items)


@router.post("/run", response_model=RunResult)
async def run_now(
    user: CurrentUserDep,
    session: SessionDep,
    providers: ProvidersDep,
    settings: SettingsDep,
) -> RunResult:
    """Manually run the recommendation refresh + notify for the current user (personal/testing)."""
    return await NotificationService(session, providers, settings).run_for_user(user)


@router.post("/devices", response_model=Message, status_code=status.HTTP_201_CREATED)
async def register_device(
    req: RegisterDeviceRequest, user: CurrentUserDep, session: SessionDep
) -> Message:
    await DeviceRepository(session).upsert(user.id, req.device_token, req.platform)
    return Message(message="Device registered.")


@router.delete(
    "/devices/{device_token}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def unregister_device(
    device_token: str, user: CurrentUserDep, session: SessionDep
) -> Response:
    await DeviceRepository(session).deactivate(user.id, device_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
