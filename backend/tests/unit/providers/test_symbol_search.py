from __future__ import annotations

import httpx

from app.providers.market.finnhub import FinnhubProvider
from app.providers.market.fmp import FMPProvider


class FakeClient:
    def __init__(self, payload) -> None:
        self.payload = payload

    async def get(self, url, **kwargs):
        return httpx.Response(200, json=self.payload, request=httpx.Request("GET", url))


async def test_finnhub_search_filters_and_maps_types():
    payload = {
        "count": 4,
        "result": [
            {"symbol": "AAPL", "description": "APPLE INC", "type": "Common Stock"},
            {"symbol": "SPY", "description": "SPDR S&P 500 ETF", "type": "ETP"},
            {"symbol": "AAPL.MX", "description": "APPLE (MEXICO)", "type": "Common Stock"},
            {"symbol": "SOMECRYPTO", "description": "x", "type": "Crypto"},
        ],
    }
    provider = FinnhubProvider(FakeClient(payload), "KEY")  # type: ignore[arg-type]

    hits = await provider.search_symbols("apple", 20)

    symbols = {h.symbol: h.type for h in hits}
    assert symbols == {"AAPL": "stock", "SPY": "etf"}  # dotted + crypto dropped


async def test_fmp_search_keeps_us_exchanges_only():
    payload = [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
        {"symbol": "TD", "name": "Toronto Dominion", "exchange": "TSX"},
        {"symbol": "NKE", "name": "Nike", "exchange": "NYSE"},
    ]
    provider = FMPProvider(FakeClient(payload), "KEY")  # type: ignore[arg-type]

    hits = await provider.search_symbols("a", 20)

    assert {h.symbol for h in hits} == {"AAPL", "NKE"}  # non-US TSX dropped
