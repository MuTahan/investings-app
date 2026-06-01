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
)

_BASE = "https://www.alphavantage.co/query"


class AlphaVantageProvider(BaseMarketProvider):
    name = "alphavantage"

    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        self._client = client
        self._key = api_key

    async def _get(self, params: dict) -> dict:
        params = {**params, "apikey": self._key}
        try:
            resp = await self._client.get(_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"alphavantage error: {exc}") from exc
        if "Note" in data or "Information" in data:
            raise ProviderError("alphavantage rate limit reached")
        return data

    async def get_quote(self, symbol: str) -> QuoteData:
        data = await self._get({"function": "GLOBAL_QUOTE", "symbol": symbol.upper()})
        q = data.get("Global Quote") or {}
        price = q.get("05. price")
        if not price:
            raise ProviderError(f"alphavantage: no quote for {symbol}")
        pct = q.get("10. change percent", "").replace("%", "")
        return QuoteData(
            symbol=symbol.upper(),
            price=float(price),
            change=_f(q.get("09. change")),
            change_pct=_f(pct),
            open=_f(q.get("02. open")),
            high=_f(q.get("03. high")),
            low=_f(q.get("04. low")),
            prev_close=_f(q.get("08. previous close")),
            volume=_f(q.get("06. volume")),
            as_of=datetime.now(UTC),
        )

    async def get_candles(
        self, symbol: str, resolution: str, frm: datetime, to: datetime
    ) -> CandleSeries:
        # AlphaVantage free tier: daily series is the reliable option.
        data = await self._get(
            {"function": "TIME_SERIES_DAILY", "symbol": symbol.upper(), "outputsize": "compact"}
        )
        series = data.get("Time Series (Daily)")
        if not series:
            raise ProviderError(f"alphavantage: no candles for {symbol}")
        candles: list[Candle] = []
        for day, row in series.items():
            t = datetime.fromisoformat(day).replace(tzinfo=UTC)
            if t < frm or t > to:
                continue
            candles.append(
                Candle(
                    t=t,
                    o=float(row["1. open"]),
                    h=float(row["2. high"]),
                    l=float(row["3. low"]),
                    c=float(row["4. close"]),
                    v=_f(row.get("5. volume")),
                )
            )
        candles.sort(key=lambda c: c.t)
        return CandleSeries(symbol=symbol.upper(), resolution="D", candles=candles)

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        data = await self._get({"function": "OVERVIEW", "symbol": symbol.upper()})
        if not data or "Symbol" not in data:
            raise ProviderError(f"alphavantage: no fundamentals for {symbol}")
        return Fundamentals(
            symbol=symbol.upper(),
            pe=_f(data.get("PERatio")),
            forward_pe=_f(data.get("ForwardPE")),
            eps_growth=_f(data.get("QuarterlyEarningsGrowthYOY")),
            revenue_growth=_f(data.get("QuarterlyRevenueGrowthYOY")),
            gross_margin=_f(data.get("GrossProfitTTM")),
            op_margin=_f(data.get("OperatingMarginTTM")),
            market_cap=_f(data.get("MarketCapitalization")),
            dividend_yield=_f(data.get("DividendYield")),
            beta=_f(data.get("Beta")),
            raw={k: v for k, v in data.items() if isinstance(v, str)},
        )


def _f(value: object) -> float | None:
    try:
        if value in (None, "", "None", "-"):
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
