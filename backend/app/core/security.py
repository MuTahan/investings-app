"""Password hashing, JWT issue/verify, and Apple identity-token verification."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import httpx
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings
from app.core.exceptions import Unauthorized

_ph = PasswordHasher()

TokenType = Literal["access", "refresh"]


# ---------------- password hashing ----------------
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


# ---------------- JWT ----------------
@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


def _encode(settings: Settings, sub: str, token_type: TokenType, ttl: int) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def issue_token_pair(settings: Settings, user_id: uuid.UUID | str) -> TokenPair:
    sub = str(user_id)
    return TokenPair(
        access_token=_encode(settings, sub, "access", settings.access_token_ttl_seconds),
        refresh_token=_encode(settings, sub, "refresh", settings.refresh_token_ttl_seconds),
        expires_in=settings.access_token_ttl_seconds,
    )


def issue_access_token(settings: Settings, user_id: uuid.UUID | str) -> str:
    return _encode(settings, str(user_id), "access", settings.access_token_ttl_seconds)


def decode_token(settings: Settings, token: str, expected_type: TokenType) -> str:
    """Return the subject (user id) or raise Unauthorized."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("Token expired.") from exc
    except jwt.PyJWTError as exc:
        raise Unauthorized("Invalid token.") from exc
    if payload.get("type") != expected_type:
        raise Unauthorized("Wrong token type.")
    sub = payload.get("sub")
    if not sub:
        raise Unauthorized("Malformed token.")
    return str(sub)


# ---------------- Apple Sign-In ----------------
class AppleTokenVerifier:
    """Verifies Apple identity tokens against Apple's published JWKS.

    Keys are cached in-process; Apple rotates them rarely.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None
        self._jwks_client: jwt.PyJWKClient | None = None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _get_jwks_client(self) -> jwt.PyJWKClient:
        if self._jwks_client is None:
            # PyJWKClient fetches + caches signing keys (uses urllib synchronously).
            self._jwks_client = jwt.PyJWKClient(self._settings.apple_jwks_url)
        return self._jwks_client

    async def verify(self, identity_token: str, nonce: str | None = None) -> dict[str, Any]:
        if not self._settings.apple_client_id:
            raise Unauthorized("Apple Sign-In is not configured.")
        try:
            signing_key = self._get_jwks_client().get_signing_key_from_jwt(identity_token)
            claims = jwt.decode(
                identity_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._settings.apple_client_id,
                issuer=self._settings.apple_issuer,
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized("Invalid Apple identity token.") from exc

        if nonce is not None and claims.get("nonce") != nonce:
            raise Unauthorized("Apple token nonce mismatch.")
        if not claims.get("sub"):
            raise Unauthorized("Apple token missing subject.")
        return claims
