"""Read-through cache abstraction. Redis when configured, in-memory otherwise."""

from __future__ import annotations

import json
from typing import Any, Protocol

from cachetools import TTLCache

from app.config import Settings


class Cache(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int) -> None: ...
    async def aclose(self) -> None: ...


class InMemoryCache:
    def __init__(self, maxsize: int = 4096, default_ttl: int = 600) -> None:
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=default_ttl)

    async def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        # cachetools TTL is per-cache; for MVP we accept the cache-wide TTL and store as-is.
        self._cache[key] = value

    async def aclose(self) -> None:
        self._cache.clear()


class RedisCache:
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis  # imported lazily so redis isn't required locally

        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self._redis.set(key, json.dumps(value, default=str), ex=ttl)

    async def aclose(self) -> None:
        await self._redis.aclose()


def build_cache(settings: Settings) -> Cache:
    if settings.redis_url:
        return RedisCache(settings.redis_url)
    return InMemoryCache()
