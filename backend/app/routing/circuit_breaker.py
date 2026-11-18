"""
Distributed Circuit Breaker for LLM providers.
States:
  - CLOSED: Normal operation, requests pass through.
  - OPEN: Provider is failing, reject requests immediately to prevent cascading failures.
  - HALF_OPEN: Probe state, allows a trial request to check if provider has recovered.
"""
from __future__ import annotations

import time
from enum import Enum
from typing import Optional
import structlog

from app.redis.client import get_redis_client
from app.core.metrics import CIRCUIT_BREAKER_STATE

logger = structlog.get_logger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Manages circuit breaker state per provider in Redis."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 45,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold = success_threshold

    async def get_state(self, provider_id: str) -> CircuitState:
        redis = await get_redis_client()
        key = f"cb:{provider_id}"

        state_str = await redis.hget(key, "state")
        if not state_str:
            return CircuitState.CLOSED

        state = CircuitState(state_str)
        if state == CircuitState.OPEN:
            opened_at = float(await redis.hget(key, "opened_at") or 0)
            if time.time() - opened_at >= self.recovery_timeout_seconds:
                # Transition to HALF_OPEN to probe provider
                await redis.hset(key, "state", CircuitState.HALF_OPEN.value)
                CIRCUIT_BREAKER_STATE.labels(provider=provider_id).set(1)  # 0=closed, 1=half_open, 2=open
                return CircuitState.HALF_OPEN

        return state

    async def record_success(self, provider_id: str) -> None:
        redis = await get_redis_client()
        key = f"cb:{provider_id}"
        state = await self.get_state(provider_id)

        if state == CircuitState.HALF_OPEN:
            consecutive_successes = await redis.hincrbyfloat(key, "consecutive_successes", 1.0)
            if consecutive_successes >= self.success_threshold:
                # Recovered back to CLOSED
                await redis.delete(key)
                CIRCUIT_BREAKER_STATE.labels(provider=provider_id).set(0)
                logger.info("Circuit breaker reset to CLOSED", provider_id=provider_id)
        elif state == CircuitState.CLOSED:
            # Reset failure count after clean success
            await redis.hdel(key, "failures")

    async def record_failure(self, provider_id: str) -> None:
        redis = await get_redis_client()
        key = f"cb:{provider_id}"
        state = await self.get_state(provider_id)

        if state == CircuitState.HALF_OPEN:
            # Probe failed, reopen circuit immediately
            await redis.hset(key, "state", CircuitState.OPEN.value)
            await redis.hset(key, "opened_at", str(time.time()))
            CIRCUIT_BREAKER_STATE.labels(provider=provider_id).set(2)
            logger.warning("Probe failed: circuit reopened to OPEN", provider_id=provider_id)
            return

        failures = await redis.hincrbyfloat(key, "failures", 1.0)
        if failures >= self.failure_threshold:
            await redis.hset(key, "state", CircuitState.OPEN.value)
            await redis.hset(key, "opened_at", str(time.time()))
            CIRCUIT_BREAKER_STATE.labels(provider=provider_id).set(2)
            logger.error(
                "Circuit breaker tripped to OPEN",
                provider_id=provider_id,
                failures=failures,
            )


_global_cb: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    global _global_cb
    if _global_cb is None:
        _global_cb = CircuitBreaker()
    return _global_cb

