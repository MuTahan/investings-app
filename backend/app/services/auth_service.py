from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import Conflict, Forbidden, Unauthorized
from app.core.security import (
    AppleTokenVerifier,
    TokenPair,
    decode_token,
    hash_password,
    issue_access_token,
    issue_token_pair,
    verify_password,
)
from app.db.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AppleSignInRequest, LoginRequest, RegisterRequest


class AuthService:
    def __init__(
        self, session: AsyncSession, settings: Settings, apple_verifier: AppleTokenVerifier
    ) -> None:
        self._session = session
        self._settings = settings
        self._apple = apple_verifier
        self._users = UserRepository(session)

    async def register(self, req: RegisterRequest) -> tuple[User, TokenPair]:
        if not self._settings.registration_enabled:
            raise Forbidden("Registration is disabled.")
        if await self._users.get_by_email(req.email):
            raise Conflict("An account with this email already exists.")
        user = await self._users.create(
            email=req.email,
            password_hash=hash_password(req.password),
            display_name=req.display_name,
        )
        return user, issue_token_pair(self._settings, user.id)

    async def login(self, req: LoginRequest) -> tuple[User, TokenPair]:
        user = await self._users.get_by_email(req.email)
        if user is None or not user.password_hash:
            raise Unauthorized("Invalid email or password.")
        if not verify_password(req.password, user.password_hash):
            raise Unauthorized("Invalid email or password.")
        if not user.is_active:
            raise Unauthorized("Account is disabled.")
        return user, issue_token_pair(self._settings, user.id)

    async def apple_sign_in(self, req: AppleSignInRequest) -> tuple[User, TokenPair]:
        claims = await self._apple.verify(req.identity_token, nonce=req.nonce)
        apple_sub = claims["sub"]
        email = claims.get("email")

        user = await self._users.get_by_apple_sub(apple_sub)
        if user is None and email:
            # Link to an existing email account if one exists.
            user = await self._users.get_by_email(email)
            if user is not None:
                user.apple_sub = apple_sub
                await self._users.flush()
        if user is None:
            user = await self._users.create(
                email=email,
                apple_sub=apple_sub,
                display_name=req.full_name,
            )
        return user, issue_token_pair(self._settings, user.id)

    async def refresh(self, refresh_token: str) -> tuple[str, int]:
        user_id = decode_token(self._settings, refresh_token, "refresh")
        access = issue_access_token(self._settings, user_id)
        return access, self._settings.access_token_ttl_seconds
