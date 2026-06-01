"""Simple async token-bucket rate limiter, one bucket per vendor key."""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int) -> None:
        self._rate = rate_per_sec
        self._capacity = capacity
        self._tokens = float(capacity)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Non-blocking: returns True if a token was available, else False."""
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._rate)
            self._updated = now
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False


class RateLimiterRegistry:
    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}

    def register(self, key: str, rate_per_sec: float, capacity: int) -> None:
        self._buckets[key] = TokenBucket(rate_per_sec, capacity)

    async def allow(self, key: str) -> bool:
        bucket = self._buckets.get(key)
        if bucket is None:
            return True  # unconfigured vendors are unthrottled
        return await bucket.acquire()
