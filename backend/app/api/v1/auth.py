from __future__ import annotations

from fastapi import APIRouter, status

from app.deps import ProvidersDep, SessionDep, SettingsDep
from app.schemas.auth import (
    AccessTokenResponse,
    AppleSignInRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user, token_pair) -> TokenResponse:
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
        user=UserPublic(id=user.id, email=user.email, display_name=user.display_name),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest, session: SessionDep, settings: SettingsDep, providers: ProvidersDep
) -> TokenResponse:
    service = AuthService(session, settings, providers.apple_verifier)
    user, tokens = await service.register(req)
    return _token_response(user, tokens)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest, session: SessionDep, settings: SettingsDep, providers: ProvidersDep
) -> TokenResponse:
    service = AuthService(session, settings, providers.apple_verifier)
    user, tokens = await service.login(req)
    return _token_response(user, tokens)


@router.post("/apple", response_model=TokenResponse)
async def apple_sign_in(
    req: AppleSignInRequest, session: SessionDep, settings: SettingsDep, providers: ProvidersDep
) -> TokenResponse:
    service = AuthService(session, settings, providers.apple_verifier)
    user, tokens = await service.apple_sign_in(req)
    return _token_response(user, tokens)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    req: RefreshRequest, session: SessionDep, settings: SettingsDep, providers: ProvidersDep
) -> AccessTokenResponse:
    service = AuthService(session, settings, providers.apple_verifier)
    access, expires_in = await service.refresh(req.refresh_token)
    return AccessTokenResponse(access_token=access, expires_in=expires_in)
