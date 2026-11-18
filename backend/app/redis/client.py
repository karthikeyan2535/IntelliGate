"""
Redis connection management for IntelliGate.
Provides async Redis client with connection pooling and graceful shutdown.
Supports mock/in-memory fallback when Redis is not running locally in test/dev.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)

_redis_client = None
_in_memory_store: dict[str, Any] = {}
_in_memory_expiry: dict[str, float] = {}


class InMemoryRedisFallback:
    """Lightweight in-memory Redis fallback for development/testing without Redis."""

    def __init__(self):
        self._hash_store: dict[str, dict[str, Any]] = {}
        self._zset_store: dict[str, list[tuple[str, float]]] = {}
        self._kv_store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            return self._kv_store.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        async with self._lock:
            self._kv_store[key] = str(value)
            return True

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                if k in self._kv_store:
                    del self._kv_store[k]
                    count += 1
                if k in self._hash_store:
                    del self._hash_store[k]
                    count += 1
                if k in self._zset_store:
                    del self._zset_store[k]
                    count += 1
            return count

    async def hget(self, key: str, field: str) -> Optional[str]:
        async with self._lock:
            h = self._hash_store.get(key, {})
            val = h.get(field)
            return str(val) if val is not None else None

    async def hset(self, key: str, field: str, value: Any) -> int:
        async with self._lock:
            if key not in self._hash_store:
                self._hash_store[key] = {}
            self._hash_store[key][field] = str(value)
            return 1

    async def hincrbyfloat(self, key: str, field: str, amount: float) -> float:
        async with self._lock:
            if key not in self._hash_store:
                self._hash_store[key] = {}
            curr = float(self._hash_store[key].get(field, 0.0))
            new_val = curr + float(amount)
            self._hash_store[key][field] = str(new_val)
            return new_val

    async def hdel(self, key: str, *fields: str) -> int:
        async with self._lock:
            h = self._hash_store.get(key, {})
            deleted = 0
            for f in fields:
                if f in h:
                    del h[f]
                    deleted += 1
            return deleted

    async def eval(self, script: str, numkeys: int, *keys_and_args: Any) -> Any:
        """Simulate the sliding-window rate limit and budget scripts."""
        async with self._lock:
            # We provide high-fidelity emulation for our standard Lua scripts
            keys = keys_and_args[:numkeys]
            args = keys_and_args[numkeys:]
            key = keys[0] if keys else "default"

            # 1. Rate limiter sliding window: limit, window, now
            if "ZREMRANGEBYSCORE" in script:
                limit = float(args[0])
                window = float(args[1])
                now = float(args[2])
                window_start = now - window

                entries = self._zset_store.get(key, [])
                entries = [e for e in entries if e[1] > window_start]
                self._zset_store[key] = entries

                count = len(entries)
                if count >= limit:
                    oldest_score = entries[0][1] if entries else now
                    retry_after = max(1, int(oldest_score + window - now))
                    return [0, retry_after, count]

                entries.append((f"{now}", now))
                self._zset_store[key] = entries
                return [1, 0, count + 1]

            # 2. Budget reservation: limit, amount, reservation_id
            if "total_committed" in script:
                limit = float(args[0])
                amount = float(args[1])
                res_id = str(args[2])

                h = self._hash_store.setdefault(key, {})
                used = float(h.get("used", 0.0))
                reserved = float(h.get("reserved", 0.0))
                total_committed = used + reserved

                if total_committed + amount > limit:
                    return [0, limit - total_committed]

                h[f"reserved_{res_id}"] = str(amount)
                h["reserved"] = str(reserved + amount)
                return [1, limit - total_committed - amount]

            # 3. Budget settlement: reservation_id, actual_cost (2 arguments)
            if ("actual_cost" in script or ("reserved_" in script and "HDEL" in script)) and len(args) >= 2:
                res_id = str(args[0])
                actual_cost = float(args[1])

                h = self._hash_store.setdefault(key, {})
                reserved_amount = float(h.get(f"reserved_{res_id}", 0.0))
                if reserved_amount <= 0:
                    return 0

                curr_reserved = float(h.get("reserved", 0.0))
                curr_used = float(h.get("used", 0.0))

                h["reserved"] = str(max(0.0, curr_reserved - reserved_amount))
                h["used"] = str(curr_used + actual_cost)
                h.pop(f"reserved_{res_id}", None)
                return 1

            # 4. Budget release: reservation_id (1 argument)
            if "reserved_" in script and "HDEL" in script and len(args) == 1:
                res_id = str(args[0])
                h = self._hash_store.setdefault(key, {})
                reserved_amount = float(h.get(f"reserved_{res_id}", 0.0))
                if reserved_amount <= 0:
                    return 0

                curr_reserved = float(h.get("reserved", 0.0))
                h["reserved"] = str(max(0.0, curr_reserved - reserved_amount))
                h.pop(f"reserved_{res_id}", None)
                return 1

            return [1, 0, 0]

    async def aclose(self):
        pass


async def get_redis_client():
    """Get active async Redis client, or fallback to in-memory if Redis is unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis.asyncio as aioredis
        from app.core.config import settings

        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1.5,
        )
        # Verify connection
        await client.ping()
        _redis_client = client
        logger.info("Connected to Redis successfully", url=settings.REDIS_URL)
        return _redis_client
    except Exception as exc:
        logger.warning(
            "Redis connection failed, activating in-memory fallback",
            error=str(exc),
        )
        _redis_client = InMemoryRedisFallback()
        return _redis_client


async def close_redis_client():
    """Close Redis client on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
