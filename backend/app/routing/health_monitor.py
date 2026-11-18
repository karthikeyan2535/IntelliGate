"""
Provider health monitoring and metrics aggregation.
Maintains running latency, error rates, and availability scores for intelligent routing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
import structlog

from app.redis.client import get_redis_client
from app.core.metrics import PROVIDER_HEALTH

logger = structlog.get_logger(__name__)


@dataclass
class ProviderHealthSnapshot:
    provider_id: str
    is_healthy: bool
    avg_latency_ms: float
    error_rate: float
    last_checked_at: float


class HealthMonitor:
    """Tracks provider latency and reliability."""

    async def record_request_metrics(
        self,
        provider_id: str,
        latency_ms: float,
        success: bool,
    ) -> None:
        redis = await get_redis_client()
        key = f"health:{provider_id}"

        await redis.hincrbyfloat(key, "total_requests", 1.0)
        if not success:
            await redis.hincrbyfloat(key, "failed_requests", 1.0)

        # Update running exponential moving average for latency
        curr_lat = float(await redis.hget(key, "ema_latency") or latency_ms)
        new_lat = (curr_lat * 0.8) + (latency_ms * 0.2)
        await redis.hset(key, "ema_latency", str(round(new_lat, 2)))
        await redis.hset(key, "last_seen", str(time.time()))

        # Update Prometheus gauge: 1=healthy, 0=unhealthy
        PROVIDER_HEALTH.labels(provider=provider_id).set(1 if success else 0)

    async def get_health_snapshot(self, provider_id: str) -> ProviderHealthSnapshot:
        redis = await get_redis_client()
        key = f"health:{provider_id}"

        total = float(await redis.hget(key, "total_requests") or 0.0)
        failed = float(await redis.hget(key, "failed_requests") or 0.0)
        ema_lat = float(await redis.hget(key, "ema_latency") or 250.0)
        last_seen = float(await redis.hget(key, "last_seen") or time.time())

        error_rate = (failed / total) if total > 0 else 0.0
        is_healthy = error_rate < 0.25

        return ProviderHealthSnapshot(
            provider_id=provider_id,
            is_healthy=is_healthy,
            avg_latency_ms=ema_lat,
            error_rate=error_rate,
            last_checked_at=last_seen,
        )


_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor

