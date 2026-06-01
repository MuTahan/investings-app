from __future__ import annotations

from httpx import AsyncClient


async def test_portfolio_lifecycle_and_summary(client: AsyncClient, auth_headers):
    add = await client.post(
        "/api/v1/portfolio/holdings",
        json={"symbol": "AAPL", "quantity": 10, "avg_cost": 90.0},
        headers=auth_headers,
    )
    assert add.status_code == 201

    portfolio = await client.get("/api/v1/portfolio", headers=auth_headers)
    assert portfolio.status_code == 200
    body = portfolio.json()
    assert len(body["holdings"]) == 1
    holding = body["holdings"][0]
    # fake quote price = 100, cost 90, qty 10 -> value 1000, pl 100
    assert holding["market_value"] == 1000.0
    assert holding["unrealized_pl"] == 100.0
    assert body["summary"]["market_value"] == 1000.0
    assert body["summary"]["unrealized_pl"] == 100.0
    holding_id = holding["id"]

    upd = await client.put(
        f"/api/v1/portfolio/holdings/{holding_id}",
        json={"quantity": 20, "avg_cost": 90.0},
        headers=auth_headers,
    )
    assert upd.status_code == 200

    portfolio2 = await client.get("/api/v1/portfolio", headers=auth_headers)
    assert portfolio2.json()["holdings"][0]["quantity"] == 20.0

    delete = await client.delete(f"/api/v1/portfolio/holdings/{holding_id}", headers=auth_headers)
    assert delete.status_code == 204

    empty = await client.get("/api/v1/portfolio", headers=auth_headers)
    assert empty.json()["holdings"] == []


async def test_add_duplicate_holding_conflicts(client: AsyncClient, auth_headers):
    payload = {"symbol": "MSFT", "quantity": 5, "avg_cost": 100.0}
    assert (
        await client.post("/api/v1/portfolio/holdings", json=payload, headers=auth_headers)
    ).status_code == 201
    dup = await client.post("/api/v1/portfolio/holdings", json=payload, headers=auth_headers)
    assert dup.status_code == 409
