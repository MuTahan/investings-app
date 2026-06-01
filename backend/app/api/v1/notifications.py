from __future__ import annotations

from fastapi import APIRouter, Query, Response, status
from pydantic import BaseModel, Field

from app.deps import CurrentUserDep, ProvidersDep, SessionDep, SettingsDep
from app.repositories.device_repo import DeviceRepository
from app.schemas.common import Message
from app.schemas.notification import NotificationFeedResponse, RunResult
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class RegisterDeviceRequest(BaseModel):
    device_token: str = Field(min_length=1, max_length=400)
    platform: str = "ios"


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
