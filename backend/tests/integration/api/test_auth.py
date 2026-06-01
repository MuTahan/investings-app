from __future__ import annotations

from httpx import AsyncClient

from app.config import get_settings


async def test_registration_can_be_disabled(client: AsyncClient):
    get_settings().registration_enabled = False
    resp = await client.post(
        "/api/v1/auth/register", json={"email": "blocked@example.com", "password": "password123"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_register_login_me_flow(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "password123", "display_name": "Ada"},
    )
    assert reg.status_code == 201, reg.text
    tokens = reg.json()
    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["user"]["email"] == "a@b.com"

    login = await client.post(
        "/api/v1/auth/login", json={"email": "a@b.com", "password": "password123"}
    )
    assert login.status_code == 200

    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "a@b.com"
    assert body["risk_profile"]["risk_tolerance"] == "moderate"


async def test_duplicate_register_conflicts(client: AsyncClient):
    payload = {"email": "dup@b.com", "password": "password123"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


async def test_wrong_password_unauthorized(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={"email": "c@b.com", "password": "password123"})
    bad = await client.post(
        "/api/v1/auth/login", json={"email": "c@b.com", "password": "wrongpass1"}
    )
    assert bad.status_code == 401


async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_refresh_returns_new_access_token(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register", json={"email": "r@b.com", "password": "password123"}
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_apple_sign_in(client: AsyncClient):
    resp = await client.post("/api/v1/auth/apple", json={"identity_token": "fake", "nonce": None})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == "apple.user@example.com"
