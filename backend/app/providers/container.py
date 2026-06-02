"""Long-lived container wiring providers, cache, rate limits, and the LLM.

Created once at app startup (see app/main.py lifespan) and shared across requests so
the underlying httpx client and cache are reused.
"""

from __future__ import annotations

import httpx

from app.config import Settings
from app.core.logging import get_logger
from app.core.security import AppleTokenVerifier
from app.notifications.notifier import CompositeNotifier, build_notifier
from app.providers.base import LLMProvider, MarketDataProvider
from app.providers.cache import build_cache
from app.providers.llm.anthropic_provider import AnthropicProvider
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.llm.stub import StubLLMProvider
from app.providers.market.alphavantage import AlphaVantageProvider
from app.providers.market.finnhub import FinnhubProvider
from app.providers.market.fmp import FMPProvider
from app.providers.market.newsapi import NewsAPIProvider
from app.providers.market.twelvedata import TwelveDataProvider
from app.providers.rate_limit import RateLimiterRegistry
from app.providers.router import MarketDataRouter

logger = get_logger("providers.container")

# Conservative defaults to stay under free-tier quotas: (rate_per_sec, burst_capacity)
_RATE_LIMITS: dict[str, tuple[float, int]] = {
    "finnhub": (1.0, 30),
    "alphavantage": (0.08, 5),  # ~5 calls/min on the free tier
    "fmp": (3.0, 10),
    "newsapi": (0.5, 5),
}


class ProviderContainer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=15.0)

        market = self._build_market_providers()
        rate_limiter = RateLimiterRegistry()
        for name, (rate, cap) in _RATE_LIMITS.items():
            rate_limiter.register(name, rate, cap)

        self.cache = build_cache(settings)
        self.market = MarketDataRouter(
            settings, self.cache, rate_limiter, self._build_chains(market)
        )
        self.market_vendors = [p.name for p in market]
        self.llm: LLMProvider = self._build_llm()
        self.apple_verifier = AppleTokenVerifier(settings, client=self._client)
        self.notifier: CompositeNotifier = build_notifier(settings, self._client)
        logger.info(
            "providers_ready",
            extra={
                "market_vendors": self.market_vendors,
                "llm": self.llm.name,
                "notifier_channels": self.notifier.channels,
                "cache": type(self.cache).__name__,
            },
        )

    def _build_market_providers(self) -> list[MarketDataProvider]:
        s = self._settings
        providers: list[MarketDataProvider] = []
        if s.finnhub_api_key:
            providers.append(FinnhubProvider(self._client, s.finnhub_api_key))
        if s.fmp_api_key:
            providers.append(FMPProvider(self._client, s.fmp_api_key))
        if s.alphavantage_api_key:
            providers.append(AlphaVantageProvider(self._client, s.alphavantage_api_key))
        if s.twelvedata_api_key:
            providers.append(TwelveDataProvider(self._client, s.twelvedata_api_key))
        if s.newsapi_api_key:
            providers.append(NewsAPIProvider(self._client, s.newsapi_api_key))
        return providers

    def _build_chains(
        self, providers: list[MarketDataProvider]
    ) -> dict[str, list[MarketDataProvider]]:
        by_name = {p.name: p for p in providers}

        def chain(*names: str) -> list[MarketDataProvider]:
            return [by_name[n] for n in names if n in by_name]

        return {
            "quote": chain("finnhub", "fmp", "twelvedata", "alphavantage"),
            # FMP serves daily (free); it raises on intraday so the router falls
            # through to Twelve Data (the only free intraday source).
            "candles": chain("fmp", "twelvedata", "alphavantage", "finnhub"),
            "fundamentals": chain("finnhub", "fmp", "alphavantage"),
            "news": chain("finnhub", "newsapi"),
            "search": chain("finnhub", "fmp", "twelvedata"),
        }

    def _build_llm(self) -> LLMProvider:
        s = self._settings
        choice = s.llm_provider

        # Explicit selection wins; falls back to the stub if its key is missing.
        if choice == "anthropic" and s.anthropic_api_key:
            return AnthropicProvider(self._client, s.anthropic_api_key)
        if choice == "openai" and s.openai_api_key:
            return OpenAIProvider(self._client, s.openai_api_key)
        if choice == "google" and s.google_api_key:
            return GeminiProvider(self._client, s.google_api_key)
        if choice == "stub":
            return StubLLMProvider()

        # "auto": first configured key wins.
        if choice == "auto":
            if s.anthropic_api_key:
                return AnthropicProvider(self._client, s.anthropic_api_key)
            if s.openai_api_key:
                return OpenAIProvider(self._client, s.openai_api_key)
            if s.google_api_key:
                return GeminiProvider(self._client, s.google_api_key)
        return StubLLMProvider()

    async def aclose(self) -> None:
        await self._client.aclose()
        await self.cache.aclose()
