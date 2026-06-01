from __future__ import annotations

from app.providers.rate_limit import RateLimiterRegistry, TokenBucket


async def test_token_bucket_allows_up_to_capacity():
    bucket = TokenBucket(rate_per_sec=0.0, capacity=3)
    assert await bucket.acquire()
    assert await bucket.acquire()
    assert await bucket.acquire()
    assert not await bucket.acquire()  # exhausted, no refill at rate 0


async def test_registry_unconfigured_key_allows():
    registry = RateLimiterRegistry()
    assert await registry.allow("unknown-vendor")


async def test_registry_configured_key_throttles():
    registry = RateLimiterRegistry()
    registry.register("vendor", rate_per_sec=0.0, capacity=1)
    assert await registry.allow("vendor")
    assert not await registry.allow("vendor")
