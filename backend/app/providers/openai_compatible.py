"""
OpenAI-compatible provider adapter for local inference servers.

Works with Ollama, vLLM, LM Studio, llama.cpp, etc.
Inherits from OpenAIProvider and overrides only what differs.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.providers.base import ProviderError, ProviderMessage
from app.providers.openai_provider import OpenAIProvider

logger = structlog.get_logger(__name__)


class OpenAICompatibleProvider(OpenAIProvider):
    """
    Generic OpenAI-compatible adapter.

    Use for local inference servers (Ollama, vLLM, LM Studio) that expose
    an OpenAI-compatible /v1/chat/completions endpoint at a custom base URL.
    """

    provider_type = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str = "not-required",  # many local servers don't need auth
        timeout: float = 180.0,  # local servers can be slow on first token
        organization: str | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            organization=organization,
        )

    # ------------------------------------------------------------------
    # Override: more lenient HTTP client (optional auth)
    # ------------------------------------------------------------------

    def _build_client(self, timeout: float | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json"}

        # Only add Authorization if a real key was provided
        if self._api_key and self._api_key not in {
            "not-required",
            "none",
            "",
            "ollama",
        }:
            headers["Authorization"] = f"Bearer {self._api_key}"

        if self._organization:
            headers["OpenAI-Organization"] = self._organization

        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout or self._timeout),
        )

    # ------------------------------------------------------------------
    # Override: more lenient error handling for local servers
    # ------------------------------------------------------------------

    def _map_status_to_error(
        self, status_code: int, message: str, error_code: str
    ) -> ProviderError:
        # Local servers may return non-standard codes; be more forgiving
        retryable = status_code in {429, 500, 502, 503, 504, 0}
        if status_code == 401:
            error_code = "auth_error"
        elif status_code == 429:
            error_code = "rate_limit"
        elif status_code in {400, 422}:
            error_code = "validation_error"
            retryable = False
        return ProviderError(
            message,
            status_code=status_code,
            error_code=error_code,
            retryable=retryable,
            provider=self.provider_type,
        )

    # ------------------------------------------------------------------
    # Token estimation — no tiktoken dependency assumption for local models
    # ------------------------------------------------------------------

    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        total = 0
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            total += max(1, int(len(content.split()) * 1.33)) + 4
        return total + 2

    # ------------------------------------------------------------------
    # Health check — try /v1/models, fall back to a simple ping
    # ------------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        import time

        start = time.monotonic()
        try:
            async with self._build_client(timeout=5.0) as client:
                resp = await client.get("/v1/models")
            latency_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return {"healthy": True, "latency_ms": latency_ms, "detail": "ok"}
            # Some servers don't expose /v1/models → try root ping
            async with self._build_client(timeout=5.0) as client:
                resp = await client.get("/")
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "healthy": resp.status_code < 500,
                "latency_ms": latency_ms,
                "detail": f"HTTP {resp.status_code}",
            }
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return {"healthy": False, "latency_ms": latency_ms, "detail": str(exc)}
