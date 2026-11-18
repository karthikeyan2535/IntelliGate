"""
Distributed multi-tier rate limiting for IntelliGate using Redis sliding windows.
Enforces limits at Organization, Project, and Virtual API Key levels (RPM, TPM, Daily, Monthly).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
import structlog

from app.redis.client import get_redis_client
from app.redis.lua_scripts import SLIDING_WINDOW_RATE_LIMIT_LUA
from app.core.metrics import RATE_LIMIT_REJECTIONS_TOTAL

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0
    limit_type: str = ""
    current_count: int = 0
    limit_value: int = 0


class RateLimiter:
    """Enforces multi-tier sliding-window rate limits in Redis."""

    def __init__(self):
        pass

    async def check_rate_limits(
        self,
        organization_id: str,
        project_id: Optional[str] = None,
        virtual_key_id: Optional[str] = None,
        key_rpm_limit: Optional[int] = None,
        key_tpm_limit: Optional[int] = None,
        estimated_tokens: int = 0,
        org_rpm_limit: Optional[int] = 600,
        org_tpm_limit: Optional[int] = 1_000_000,
    ) -> RateLimitResult:
        """
        Evaluates tiered rate limits:
        1. Virtual Key RPM / TPM
        2. Organization RPM / TPM
        Returns RateLimitResult with earliest retry interval if throttled.
        """
        redis = await get_redis_client()
        now = time.time()

        checks: list[tuple[str, int, int, str]] = []  # (redis_key, limit, window, limit_name)

        # 1. Virtual API Key checks
        if virtual_key_id:
            if key_rpm_limit and key_rpm_limit > 0:
                checks.append((f"rl:key:{virtual_key_id}:rpm", key_rpm_limit, 60, "key_rpm"))
            if key_tpm_limit and key_tpm_limit > 0 and estimated_tokens > 0:
                # We check token bucket or TPM approximation
                token_limit = max(1, key_tpm_limit // max(1, estimated_tokens))
                checks.append((f"rl:key:{virtual_key_id}:tpm", token_limit, 60, "key_tpm"))

        # 2. Organization checks
        if organization_id:
            if org_rpm_limit and org_rpm_limit > 0:
                checks.append((f"rl:org:{organization_id}:rpm", org_rpm_limit, 60, "org_rpm"))
            if org_tpm_limit and org_tpm_limit > 0 and estimated_tokens > 0:
                org_token_limit = max(1, org_tpm_limit // max(1, estimated_tokens))
                checks.append((f"rl:org:{organization_id}:tpm", org_token_limit, 60, "org_tpm"))

        # Execute atomic sliding window script for each configured limit
        for r_key, limit_val, window_sec, limit_type in checks:
            try:
                res = await redis.eval(
                    SLIDING_WINDOW_RATE_LIMIT_LUA,
                    1,
                    r_key,
                    limit_val,
                    window_sec,
                    now,
                )
                allowed = int(res[0]) == 1
                retry_after = int(res[1])
                curr_count = int(res[2])

                if not allowed:
                    RATE_LIMIT_REJECTIONS_TOTAL.inc()
                    logger.warning(
                        "Rate limit exceeded",
                        key=r_key,
                        limit_type=limit_type,
                        limit=limit_val,
                        retry_after=retry_after,
                    )
                    return RateLimitResult(
                        allowed=False,
                        retry_after_seconds=max(1, retry_after),
                        limit_type=limit_type,
                        current_count=curr_count,
                        limit_value=limit_val,
                    )
            except Exception as exc:
                logger.error("Rate limiter Redis script evaluation failed", error=str(exc))
                # Fail-open for transient Redis blips or continue to next check

        return RateLimitResult(allowed=True)

