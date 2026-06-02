from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import (
    BaseMarketProvider,
    Candle,
    CandleSeries,
    Fundamentals,
    QuoteData,
    SymbolHit,
)

_US_EXCHANGES = {"NASDAQ", "NYSE", "AMEX", "NYSE AMERICAN", "BATS", "OTC"}

# FMP migrated off /api/v3 to the "stable" API (query-param based).
_BASE = "https://financialmodelingprep.com/stable"


class FMPProvider(BaseMarketProvider):
    name = "fmp"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, path: str, params: dict | None = None) -> list | dict:
        params = {**(params or {}), "apikey": self._key}
        try:
            resp = await self._client.get(f"{_BASE}{path}", params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"fmp {path} error: {exc}") from exc

    async def search_symbols(self, query: str, limit: int) -> list[SymbolHit]:
        data = await self._get("/search-symbol", {"query": query, "limit": limit * 2})
        if not isinstance(data, list):
            return []
        hits: list[SymbolHit] = []
        for r in data:
            symbol = (r.get("symbol") or "").upper()
            exchange = (r.get("exchange") or r.get("exchangeShortName") or "").upper()
            if not symbol or "." in symbol:
                continue
            if exchange and exchange not in _US_EXCHANGES:
                continue
            hits.append(
                SymbolHit(symbol=symbol, name=r.get("name") or symbol, exchange=exchange or None)
            )
            if len(hits) >= limit:
                break
        return hits

    async def get_quote(self, symbol: str) -> QuoteData:
        data = await self._get("/quote", {"symbol": symbol.upper()})
        if not isinstance(data, list) or not data:
            raise ProviderError(f"fmp: no quote for {symbol}")
        q = data[0]
        return QuoteData(
            symbol=symbol.upper(),
            price=float(q["price"]),
            change=_f(q.get("change")),
            change_pct=_f(q.get("changePercentage")),
            open=_f(q.get("open")),
            high=_f(q.get("dayHigh")),
            low=_f(q.get("dayLow")),
            prev_close=_f(q.get("previousClose")),
            volume=_f(q.get("volume")),
            as_of=datetime.now(UTC),
        )

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        rows = await self._get(
            "/historical-price-eod/full",
            {"symbol": symbol.upper(), "from": frm.date().isoformat(), "to": to.date().isoformat()},
        )
        if not isinstance(rows, list) or not rows:
            raise ProviderError(f"fmp: no candles for {symbol}")
        candles = [
            Candle(
                t=datetime.fromisoformat(r["date"]).replace(tzinfo=UTC),
                o=float(r["open"]),
                h=float(r["high"]),
                l=float(r["low"]),
                c=float(r["close"]),
                v=_f(r.get("volume")),
            )
            for r in rows
            if r.get("open") is not None
        ]
        candles.sort(key=lambda c: c.t)
        return CandleSeries(symbol=symbol.upper(), resolution="D", candles=candles)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        ratios = await self._get("/ratios-ttm", {"symbol": symbol.upper()})
        profile = await self._get("/profile", {"symbol": symbol.upper()})
        r = ratios[0] if isinstance(ratios, list) and ratios else {}
        p = profile[0] if isinstance(profile, list) and profile else {}
        return Fundamentals(
            symbol=symbol.upper(),
            pe=_f(r.get("priceToEarningsRatioTTM") or r.get("peRatioTTM")),
            gross_margin=_f(r.get("grossProfitMarginTTM")),
            op_margin=_f(r.get("operatingProfitMarginTTM")),
            market_cap=_f(p.get("marketCap")),
            dividend_yield=_f(r.get("dividendYieldTTM")),
            beta=_f(p.get("beta")),
            raw={
                "sector": p.get("sector"),
                "industry": p.get("industry"),
                "isEtf": p.get("isEtf"),
            },
        )


def _f(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
