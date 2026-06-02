from __future__ import annotations

from httpx import AsyncClient

VALID_RATINGS = {"STRONG_BUY", "BUY", "HOLD", "WATCH", "AVOID"}


async def test_recommendation_returns_full_committee_output(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/recommendations/AAPL", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert body["rating"] in VALID_RATINGS
    assert body["anchor_rating"] in VALID_RATINGS
    assert body["decision_mode"] == "deterministic"  # FakeLLM stub -> deterministic core
    assert len(body["agent_breakdown"]) == 6
    agents = {a["agent"] for a in body["agent_breakdown"]}
    assert agents == {"news", "technical", "fundamental", "macro", "risk", "portfolio_fit"}
    assert body["reasons"] and body["risks"]
    assert body["valuation"] is not None
    assert body["valuation"]["fair_value"] is not None
    assert body["valuation"]["holding_period"]


async def test_recommendation_is_idempotent_within_freshness(client: AsyncClient, auth_headers):
    first = await client.get("/api/v1/recommendations/AAPL", headers=auth_headers)
    second = await client.get("/api/v1/recommendations/AAPL", headers=auth_headers)
    assert first.json()["rating"] == second.json()["rating"]
    assert first.json()["composite_score"] == second.json()["composite_score"]


async def test_recommendation_unknown_symbol_404(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/recommendations/ZZZZ", headers=auth_headers)
    assert resp.status_code == 404


async def test_recommendation_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/recommendations/AAPL")
    assert resp.status_code == 401


async def test_recommendation_history(client: AsyncClient, auth_headers):
    await client.get("/api/v1/recommendations/AAPL", headers=auth_headers)
    resp = await client.get("/api/v1/recommendations/AAPL/history", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 1


async def test_recommendation_scope_watchlist(client: AsyncClient, auth_headers):
    await client.post("/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers)
    resp = await client.get(
        "/api/v1/recommendations", params={"scope": "watchlist"}, headers=auth_headers
    )
    assert resp.status_code == 200
    symbols = [i["symbol"] for i in resp.json()["items"]]
    assert "AAPL" in symbols


async def test_recommendation_center_sections(client: AsyncClient, auth_headers):
    await client.post("/api/v1/watchlist/items", json={"symbol": "AAPL"}, headers=auth_headers)
    resp = await client.get("/api/v1/recommendations/center", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    for section in ("top_picks", "short_term", "long_term", "trending", "personalized"):
        assert section in body
    # every card has a valuation + reasoning; trending includes the watchlist symbol
    assert "AAPL" in [c["symbol"] for c in body["trending"]]
    card = body["trending"][0]
    assert card["valuation"] is not None and "rating" in card
