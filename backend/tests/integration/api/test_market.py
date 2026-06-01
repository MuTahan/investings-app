from __future__ import annotations

from httpx import AsyncClient


async def test_search_returns_seeded_instruments(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/market/search", params={"q": "AAPL"}, headers=auth_headers)
    assert resp.status_code == 200
    symbols = [r["symbol"] for r in resp.json()["results"]]
    assert "AAPL" in symbols


async def test_instrument_detail(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/market/instruments/AAPL", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"
    assert resp.json()["type"] == "stock"


async def test_unknown_instrument_404(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/market/instruments/ZZZZ", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_quote_uses_provider(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/market/quote/AAPL", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"
    assert resp.json()["price"] == 100.0


async def test_candles(client: AsyncClient, auth_headers):
    resp = await client.get(
        "/api/v1/market/candles/AAPL", params={"resolution": "D", "days": 30}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"
    assert len(resp.json()["candles"]) == 5


async def test_market_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/market/quote/AAPL")
    assert resp.status_code == 401
