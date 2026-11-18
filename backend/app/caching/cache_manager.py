"""
Exact-match response caching manager for IntelliGate.
Stores cached completions in Redis with serialization, TTL, and tenant isolation validation.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional
import structlog

from app.redis.client import get_redis_client
from app.core.metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL

logger = structlog.get_logger(__name__)


class CacheManager:
    """Manages exact-match response caching with strict multi-tenant validation."""

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl

    async def get(self, cache_key: str, organization_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieves cached response. Validates tenant ownership before returning.
        """
        redis = await get_redis_client()
        raw = await redis.get(cache_key)
        if not raw:
            CACHE_MISSES_TOTAL.labels(cache_type="exact").inc()
            return None

        try:
            data = json.loads(raw)
            # Strict tenant isolation check
            cached_org = data.get("organization_id")
            if str(cached_org) != str(organization_id):
                logger.error(
                    "Tenant isolation mismatch in cache lookup! Rejecting entry.",
                    expected_org=str(organization_id),
                    cached_org=str(cached_org),
                )
                return None

            CACHE_HITS_TOTAL.labels(cache_type="exact").inc()
            return data
        except Exception as exc:
            logger.warning("Failed to deserialize cache payload", error=str(exc))
            return None

    async def set(
        self,
        cache_key: str,
        organization_id: str,
        response_payload: dict[str, Any],
        usage: dict[str, Any],
        cost_usd: str,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Persists a response in the cache. Always includes organization_id in the stored envelope.
        """
        redis = await get_redis_client()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        envelope = {
            "organization_id": str(organization_id),
            "cached_at": time.time(),
            "ttl": ttl,
            "response": response_payload,
            "usage": usage,
            "cost_usd": str(cost_usd),
        }

        try:
            payload = json.dumps(envelope, ensure_ascii=True, default=str)
            await redis.set(cache_key, payload, ex=ttl)
            return True
        except Exception as exc:
            logger.warning("Failed to write to cache", error=str(exc))
            return False

    async def delete(self, cache_key: str) -> bool:
        redis = await get_redis_client()
        return bool(await redis.delete(cache_key))

    @staticmethod
    def is_cacheable(request_dict: dict[str, Any], response_dict: dict[str, Any]) -> bool:
        """
        Determines whether a request and response pair is eligible for exact caching.
        """
        # Do not cache streaming by default unless completed
        if request_dict.get("stream", False):
            return False

        # If temperature > 0, requests are non-deterministic unless zero
        temp = request_dict.get("temperature")
        if temp is not None and float(temp) > 0.0:
            return False

        # Do not cache requests with tool execution requests if dynamic
        choices = response_dict.get("choices", [])
        if choices:
            finish_reason = choices[0].get("finish_reason")
            if finish_reason == "error":
                return False

        return True

