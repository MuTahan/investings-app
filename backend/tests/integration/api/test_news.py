from __future__ import annotations

from httpx import AsyncClient


async def test_news_list(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/news", params={"symbol": "AAPL"}, headers=auth_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_news_impact_report(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/news/impact", params={"symbol": "AAPL"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert "net_sentiment" in body
    assert body["recommended_action"] in {"STRONG_BUY", "BUY", "HOLD", "WATCH", "AVOID"}
    assert isinstance(body["items"], list)


async def test_news_impact_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/news/impact", params={"symbol": "AAPL"})
    assert resp.status_code == 401
