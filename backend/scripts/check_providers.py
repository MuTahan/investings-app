"""Live provider health-check. Verifies each configured market/AI provider against
its real API, so you know exactly what's working before relying on it in production.

Run (from the backend dir, with keys in the root .env):
    docker run --rm --env-file ../.env -e PYTHONPATH=/code \
      -v "$PWD":/code -w /code investing-backend:test python scripts/check_providers.py
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx

from app.config import get_settings
from app.providers.llm.anthropic_provider import AnthropicProvider
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.market.alphavantage import AlphaVantageProvider
from app.providers.market.finnhub import FinnhubProvider
from app.providers.market.fmp import FMPProvider
from app.providers.market.newsapi import NewsAPIProvider
from app.providers.market.twelvedata import TwelveDataProvider

SYMBOL = "AAPL"


async def check_market(name: str, provider, caps: list[str]) -> None:
    to = datetime.now(UTC)
    frm = to - timedelta(days=120)
    for cap in caps:
        try:
            if cap == "quote":
                r = await provider.get_quote(SYMBOL)
                detail = f"price={r.price}"
            elif cap == "candles":
                r = await provider.get_candles(SYMBOL, "D", frm, to)
                detail = f"{len(r.candles)} candles"
            elif cap == "fundamentals":
                r = await provider.get_fundamentals(SYMBOL)
                detail = f"pe={r.pe} op_margin={r.op_margin}"
            elif cap == "news":
                r = await provider.get_news(SYMBOL, "company", 5)
                detail = f"{len(r)} articles"
            else:
                detail = "?"
            print(f"  [ OK ] {name:13} {cap:13} -> {detail}")
        except Exception as exc:  # noqa: BLE001 - report every failure
            print(f"  [FAIL] {name:13} {cap:13} -> {type(exc).__name__}: {exc}")


async def check_llm(name: str, provider, model: str) -> None:
    try:
        r = await provider.complete_json('Reply with JSON {"ok": true}.', model=model)
        print(f"  [ OK ] {name:13} model={model} -> {r}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [FAIL] {name:13} model={model} -> {type(exc).__name__}: {exc}")


async def main() -> None:
    s = get_settings()
    async with httpx.AsyncClient(timeout=25.0) as client:
        print("\n== Market data providers ==")
        if s.finnhub_api_key:
            await check_market(
                "finnhub",
                FinnhubProvider(client, s.finnhub_api_key),
                ["quote", "candles", "fundamentals", "news"],
            )
        else:
            print("  finnhub        (no key)")
        if s.fmp_api_key:
            await check_market(
                "fmp", FMPProvider(client, s.fmp_api_key), ["quote", "candles", "fundamentals"]
            )
        else:
            print("  fmp            (no key)")
        if s.alphavantage_api_key:
            await check_market(
                "alphavantage",
                AlphaVantageProvider(client, s.alphavantage_api_key),
                ["quote", "candles", "fundamentals"],
            )
        else:
            print("  alphavantage   (no key)")
        if s.twelvedata_api_key:
            await check_market(
                "twelvedata",
                TwelveDataProvider(client, s.twelvedata_api_key),
                ["quote", "candles"],
            )
        else:
            print("  twelvedata     (no key)")
        if s.newsapi_api_key:
            await check_market("newsapi", NewsAPIProvider(client, s.newsapi_api_key), ["news"])
        else:
            print("  newsapi        (no key)")

        print("\n== AI providers ==")
        if s.anthropic_api_key:
            await check_llm(
                "anthropic", AnthropicProvider(client, s.anthropic_api_key), s.ai_agent_model
            )
        else:
            print("  anthropic      (no key)")
        if s.openai_api_key:
            await check_llm("openai", OpenAIProvider(client, s.openai_api_key), "gpt-4o-mini")
        else:
            print("  openai         (no key)")
        if s.google_api_key:
            await check_llm("google", GeminiProvider(client, s.google_api_key), s.ai_chair_model)
        else:
            print("  google         (no key)")
        print(f"\n  active llm_provider = {s.llm_provider} | "
              f"agent={s.ai_agent_model} chair={s.ai_chair_model} mode={s.ai_decision_mode}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
