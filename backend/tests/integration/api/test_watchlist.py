from __future__ import annotations

from httpx import AsyncClient


async def test_watchlist_add_get_remove(client: AsyncClient, auth_headers):
    # empty initially
    empty = await client.get("/api/v1/watchlist", headers=auth_headers)
    assert empty.status_code == 200
    assert empty.json()["items"] == []

    add = await client.post(
        "/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers
    )
    assert add.status_code == 201

    listed = await client.get("/api/v1/watchlist", headers=auth_headers)
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["instrument"]["symbol"] == "AAPL"
    assert items[0]["quote"]["price"] == 100.0
    instrument_id = items[0]["instrument"]["id"]

    # duplicate -> conflict
    dup = await client.post(
        "/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers
    )
    assert dup.status_code == 409

    removed = await client.delete(f"/api/v1/watchlist/items/{instrument_id}", headers=auth_headers)
    assert removed.status_code == 204

    after = await client.get("/api/v1/watchlist", headers=auth_headers)
    assert after.json()["items"] == []


async def test_watchlist_unknown_symbol_404(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/watchlist/items", json={"symbol": "ZZZZ"}, headers=auth_headers
    )
    assert resp.status_code == 404
