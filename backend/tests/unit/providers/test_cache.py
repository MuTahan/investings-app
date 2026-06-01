from __future__ import annotations

from app.providers.cache import InMemoryCache


async def test_in_memory_cache_set_get():
    cache = InMemoryCache()
    assert await cache.get("missing") is None
    await cache.set("k", {"v": 1}, ttl=60)
    assert await cache.get("k") == {"v": 1}
    await cache.aclose()
