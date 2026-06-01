"""Application configuration, driven entirely by environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DecisionMode = Literal["deterministic", "chair_assisted", "empowered"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- app ---
    app_name: str = "Investing AI"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # --- database ---
    # async SQLAlchemy URL; postgres in prod, sqlite for tests
    database_url: str = "postgresql+asyncpg://investing:investing@db:5432/investing"

    # --- cache ---
    redis_url: str | None = None  # if None, falls back to in-memory cache

    # --- auth / security ---
    jwt_secret: str = "CHANGE_ME_DEV_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30

    # Apple Sign-In
    apple_client_id: str | None = None  # service/bundle id used as `aud`
    apple_jwks_url: str = "https://appleid.apple.com/auth/keys"
    apple_issuer: str = "https://appleid.apple.com"

    # --- market data providers (free tiers) ---
    finnhub_api_key: str | None = None
    alphavantage_api_key: str | None = None
    fmp_api_key: str | None = None
    newsapi_api_key: str | None = None

    # --- AI providers ---
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_decision_mode: DecisionMode = "empowered"
    ai_agent_model: str = "claude-haiku-4-5"
    ai_chair_model: str = "claude-sonnet-4-6"

    # --- notifications ---
    ntfy_server: str = "https://ntfy.sh"
    ntfy_topic: str | None = None  # set to enable ntfy push
    telegram_bot_token: str | None = None  # set both to enable Telegram
    telegram_chat_id: str | None = None
    app_base_url: str | None = None  # web app URL for deep-link in notifications

    # --- scheduler ---
    scheduler_enabled: bool = True
    scheduler_interval_minutes: int = 60
    notify_min_priority: Literal["normal", "high", "critical"] = "high"
    notify_max_per_run: int = 10
    quiet_hours_start: int | None = None  # 0-23 UTC; None disables quiet hours
    quiet_hours_end: int | None = None

    # --- cache TTLs (seconds) ---
    cache_ttl_quote: int = 20
    cache_ttl_candles: int = 120
    cache_ttl_fundamentals: int = 21600
    cache_ttl_news: int = 600

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
