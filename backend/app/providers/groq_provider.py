"""
Groq LLM provider adapter for IntelliGate.
Interacts with the ultra-low-latency Groq Cloud OpenAI-compatible endpoint.
"""
from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator
import httpx
import structlog

from app.providers.base import (
    BaseProvider,
    ProviderError,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    StreamChunk,
    TokenUsage,
)

logger = structlog.get_logger(__name__)

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(BaseProvider):
    """Adapter for Groq Cloud inference."""

    provider_type = "groq"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_GROQ_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "IntelliGate/1.0",
        }

    def _format_messages(self, messages: list[ProviderMessage]) -> list[dict[str, Any]]:
        formatted = []
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": self._format_messages(request.messages),
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.stop is not None:
            payload["stop"] = request.stop

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=self._headers(), json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError(f"Groq request timed out: {exc}", status_code=504, retryable=True) from exc
        except httpx.ConnectError as exc:
            raise ProviderError(f"Groq connection error: {exc}", status_code=502, retryable=True) from exc
        except Exception as exc:
            raise self.normalize_error(exc) from exc

        if res.status_code != 200:
            self._handle_error_response(res)

        data = res.json()
        choice = data["choices"][0]
        usage_data = data.get("usage", {})

        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return ProviderResponse(
            id=data.get("id", f"groq-{int(time.time())}"),
            model=data.get("model", request.model),
            content=choice.get("message", {}).get("content"),
            finish_reason=choice.get("finish_reason", "stop"),
            usage=usage,
            raw_response=data,
        )

    async def stream_completion(self, request: ProviderRequest) -> AsyncIterator[StreamChunk]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": request.model,
            "messages": self._format_messages(request.messages),
            "stream": True,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=self._headers(), json=payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        raise ProviderError(f"Groq stream error: {body.decode()}", status_code=response.status_code)

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        chunk_str = line[6:].strip()
                        if chunk_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(chunk_str)
                            choice = chunk_data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            yield StreamChunk(
                                id=chunk_data.get("id", ""),
                                model=chunk_data.get("model", request.model),
                                delta_content=delta.get("content"),
                                finish_reason=choice.get("finish_reason"),
                            )
                        except json.JSONDecodeError:
                            continue
        except Exception as exc:
            raise self.normalize_error(exc) from exc

    async def health_check(self) -> dict[str, Any]:
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, headers=self._headers())
            return {"status": "healthy" if res.status_code == 200 else "degraded", "status_code": res.status_code}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    def normalize_error(self, exc: Exception) -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        return ProviderError(message=f"Groq error: {exc}", status_code=500, retryable=False)

    def _handle_error_response(self, res: httpx.Response) -> None:
        try:
            err_json = res.json().get("error", {})
            msg = err_json.get("message", res.text)
        except Exception:
            msg = res.text

        status = res.status_code
        retryable = status in {429, 500, 502, 503, 504}
        raise ProviderError(f"Groq API error ({status}): {msg}", status_code=status, retryable=retryable)

    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        return sum(len(str(m.content).split()) * 2 for m in messages)

