from __future__ import annotations

from httpx import AsyncClient


async def test_run_returns_summary_and_feed(client: AsyncClient, auth_headers):
    await client.post("/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers)

    run = await client.post("/api/v1/notifications/run", headers=auth_headers)
    assert run.status_code == 200, run.text
    assert run.json()["evaluated"] >= 1

    feed = await client.get("/api/v1/notifications", headers=auth_headers)
    assert feed.status_code == 200
    assert "items" in feed.json()


async def test_preferences_get_and_update(client: AsyncClient, auth_headers):
    g = await client.get("/api/v1/notifications/preferences", headers=auth_headers)
    assert g.status_code == 200
    assert g.json()["min_priority"] == "high"  # default

    p = await client.put(
        "/api/v1/notifications/preferences",
        json={
            "min_priority": "low",
            "categories": ["rating_change", "news"],
            "max_risk": "high",
            "sectors": [],
            "quiet_hours_start": None,
            "quiet_hours_end": None,
        },
        headers=auth_headers,
    )
    assert p.status_code == 200
    assert p.json()["min_priority"] == "low"
    assert set(p.json()["categories"]) == {"rating_change", "news"}


async def test_run_sends_when_preference_threshold_low(client: AsyncClient, auth_headers):
    # Lower the per-user threshold so a first-time NORMAL-priority rec triggers a send.
    await client.put(
        "/api/v1/notifications/preferences",
        json={"min_priority": "normal", "categories": [], "max_risk": "high", "sectors": []},
        headers=auth_headers,
    )
    await client.post("/api/v1/watchlist/items", json={"symbol": "MSFT"}, headers=auth_headers)

    run = await client.post("/api/v1/notifications/run", headers=auth_headers)
    assert run.status_code == 200
    assert run.json()["sent"] >= 1

    feed = await client.get("/api/v1/notifications", headers=auth_headers)
    items = feed.json()["items"]
    assert len(items) >= 1
    assert items[0]["status"] == "sent"
    assert items[0]["symbol"] == "MSFT"
    assert items[0]["category"] in {"rating_change", "news"}


async def test_run_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/notifications/run")
    assert resp.status_code == 401
