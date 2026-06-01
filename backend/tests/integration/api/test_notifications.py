from __future__ import annotations

from httpx import AsyncClient

from app.config import get_settings


async def test_run_returns_summary_and_feed(client: AsyncClient, auth_headers):
    await client.post("/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers)

    run = await client.post("/api/v1/notifications/run", headers=auth_headers)
    assert run.status_code == 200, run.text
    assert run.json()["evaluated"] >= 1

    feed = await client.get("/api/v1/notifications", headers=auth_headers)
    assert feed.status_code == 200
    assert "items" in feed.json()


async def test_run_sends_and_logs_when_eligible(client: AsyncClient, auth_headers):
    # Lower the send threshold so a first-time NORMAL-priority rec triggers a send.
    get_settings().notify_min_priority = "normal"
    await client.post("/api/v1/watchlist/items", json={"symbol": "MSFT"}, headers=auth_headers)

    run = await client.post("/api/v1/notifications/run", headers=auth_headers)
    assert run.status_code == 200
    assert run.json()["sent"] >= 1

    feed = await client.get("/api/v1/notifications", headers=auth_headers)
    items = feed.json()["items"]
    assert len(items) >= 1
    assert items[0]["status"] == "sent"
    assert items[0]["symbol"] == "MSFT"


async def test_run_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/notifications/run")
    assert resp.status_code == 401
