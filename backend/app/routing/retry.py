"""
Retry handler with exponential backoff, jitter, and retryable error classification.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Coroutine
import structlog

from app.providers.base import ProviderError

logger = structlog.get_logger(__name__)


def is_retryable_error(exc: Exception) -> bool:
    """
    Classify whether an upstream error is transient and safe to retry.
    Retryable: 429 (rate limits), 500, 502, 503, 504, connection timeouts, drops.
    Non-retryable: 400 (bad request), 401 (auth), 403 (permission), 404 (model missing).
    """
    if isinstance(exc, ProviderError):
        if exc.retryable:
            return True
        if exc.status_code in {408, 429, 500, 502, 503, 504}:
            return True
        return False

    err_str = str(exc).lower()
    retryable_keywords = ["timeout", "connection reset", "broken pipe", "temporarily unavailable", "rate limit", "429"]
    return any(k in err_str for k in retryable_keywords)


async def execute_with_retry(
    operation: Callable[[], Coroutine[Any, Any, Any]],
    max_retries: int = 3,
    base_delay_seconds: float = 0.5,
    max_delay_seconds: float = 8.0,
    provider_name: str = "unknown",
) -> Any:
    """
    Executes an async provider call with exponential backoff and decorrelated jitter.
    """
    attempt = 0
    last_exception: Exception | None = None

    while attempt <= max_retries:
        try:
            return await operation()
        except Exception as exc:
            last_exception = exc
            if not is_retryable_error(exc) or attempt >= max_retries:
                logger.warning(
                    "Execution error not retryable or retries exhausted",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(exc),
                    provider=provider_name,
                )
                raise exc

            attempt += 1
            # Exponential backoff + full jitter
            backoff = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            jittered_delay = random.uniform(0.1, backoff)

            logger.info(
                "Transient error encountered, retrying after backoff",
                attempt=attempt,
                delay=round(jittered_delay, 3),
                error=str(exc),
                provider=provider_name,
            )
            await asyncio.sleep(jittered_delay)

    if last_exception:
        raise last_exception

