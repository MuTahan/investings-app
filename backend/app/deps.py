"""Shared FastAPI dependencies (DB session, settings, providers, current user)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.exceptions import Unauthorized
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_session
from app.providers.container import ProviderContainer
from app.repositories.user_repo import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_settings_dep() -> Settings:
    return get_settings()


def get_providers(request: Request) -> ProviderContainer:
    return request.app.state.providers


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
ProvidersDep = Annotated[ProviderContainer, Depends(get_providers)]


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized("Missing bearer token.")
    user_id = decode_token(settings, credentials.credentials, "access")
    user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise Unauthorized("User not found or inactive.")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
