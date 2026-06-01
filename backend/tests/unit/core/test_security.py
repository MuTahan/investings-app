from __future__ import annotations

import pytest

from app.config import Settings
from app.core.exceptions import Unauthorized
from app.core.security import (
    _encode,
    decode_token,
    hash_password,
    issue_token_pair,
    verify_password,
)

SETTINGS = Settings(jwt_secret="unit-secret", environment="test")


def test_password_hash_roundtrip():
    h = hash_password("s3cret-password")
    assert h != "s3cret-password"
    assert verify_password("s3cret-password", h)
    assert not verify_password("wrong", h)


def test_jwt_issue_and_decode():
    pair = issue_token_pair(SETTINGS, "user-123")
    assert decode_token(SETTINGS, pair.access_token, "access") == "user-123"
    assert decode_token(SETTINGS, pair.refresh_token, "refresh") == "user-123"


def test_jwt_wrong_type_rejected():
    pair = issue_token_pair(SETTINGS, "user-123")
    with pytest.raises(Unauthorized):
        decode_token(SETTINGS, pair.access_token, "refresh")


def test_jwt_expired_rejected():
    expired = _encode(SETTINGS, "user-123", "access", ttl=-10)
    with pytest.raises(Unauthorized):
        decode_token(SETTINGS, expired, "access")


def test_jwt_bad_signature_rejected():
    pair = issue_token_pair(SETTINGS, "user-123")
    other = Settings(jwt_secret="different-secret", environment="test")
    with pytest.raises(Unauthorized):
        decode_token(other, pair.access_token, "access")
