"""
OpenAI provider adapter for IntelliGate.

Uses httpx directly (no openai SDK) to avoid dependency complexity.
Supports chat completions, streaming, tools, response_format.
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

# Token estimation models
_TIKTOKEN_ENCODING_CACHE: dict[str, Any] = {}


def _get_encoding(model: str) -> Any:
    """Return the tiktoken encoding for the given model, cached."""
    import tiktoken  # optional dependency

    if model in _TIKTOKEN_ENCODING_CACHE:
        return _TIKTOKEN_ENCODING_CACHE[model]

    if "gpt-4o" in model or "o1" in model or "o3" in model:
        enc_name = "o200k_base"
    else:
        enc_name = "cl100k_base"

    enc = tiktoken.get_encoding(enc_name)
    _TIKTOKEN_ENCODING_CACHE[model] = enc
    return enc


def _map_finish_reason(raw: str | None) -> str:
    mapping = {
        "stop": "stop",
        "length": "length",
        "tool_calls": "tool_calls",
        "function_call": "tool_calls",
        "content_filter": "content_filter",
    }
    return mapping.get(raw or "", "stop")


class OpenAIProvider(BaseProvider):
    """OpenAI-compatible provider adapter."""

    provider_type = "openai"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 120.0,
        organization: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._organization = organization

    # ------------------------------------------------------------------
    # HTTP client factory (new client per call keeps things simple & safe)
    # ------------------------------------------------------------------

    def _build_client(self, timeout: float | None = None) -> httpx.AsyncClient:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._organization:
            headers["OpenAI-Organization"] = self._organization

        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout or self._timeout),
        )

    # ------------------------------------------------------------------
    # Request payload builder
    # ------------------------------------------------------------------

    def _build_payload(self, request: ProviderRequest) -> dict[str, Any]:
        messages = []
        for m in request.messages:
            msg: dict[str, Any] = {"role": m.role, "content": m.content}
            messages.append(msg)

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "stream": request.stream,
        }

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.stop:
            payload["stop"] = request.stop
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in request.tools
            ]
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.response_format is not None:
            payload["response_format"] = request.response_format

        payload.update(request.extra_params)
        return payload

    # ------------------------------------------------------------------
    # Non-streaming completion
    # ------------------------------------------------------------------

    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        payload = self._build_payload(request)
        payload["stream"] = False

        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("openai.chat_completion.start")

        async with self._build_client() as client:
            try:
                resp = await client.post("/chat/completions", json=payload)
            except httpx.TimeoutException as exc:
                raise self.normalize_error(exc)
            except httpx.RequestError as exc:
                raise self.normalize_error(exc)

        if resp.status_code != 200:
            raise self._raise_from_response(resp)

        data: dict = resp.json()
        choice = data["choices"][0]
        message = choice.get("message", {})

        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            cached_tokens=usage_data.get("prompt_tokens_details", {}).get(
                "cached_tokens", 0
            ),
            reasoning_tokens=usage_data.get("completion_tokens_details", {}).get(
                "reasoning_tokens", 0
            ),
        )

        return ProviderResponse(
            id=data.get("id", ""),
            model=data.get("model", request.model),
            content=message.get("content"),
            finish_reason=_map_finish_reason(choice.get("finish_reason")),
            tool_calls=message.get("tool_calls"),
            usage=usage,
            raw_response=data,
        )

    # ------------------------------------------------------------------
    # Streaming completion
    # ------------------------------------------------------------------

    async def stream_completion(
        self, request: ProviderRequest
    ) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(request)
        payload["stream"] = True
        payload["stream_options"] = {"include_usage": True}

        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("openai.stream_completion.start")

        async with self._build_client() as client:
            try:
                async with client.stream(
                    "POST", "/chat/completions", json=payload
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise self._raise_from_bytes(resp.status_code, body)

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        raw = line[6:]
                        if raw == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(raw)
                        except json.JSONDecodeError:
                            log.warning("openai.stream.bad_json", raw=raw)
                            continue

                        chunk_id = chunk_data.get("id", "")
                        chunk_model = chunk_data.get("model", request.model)
                        choices = chunk_data.get("choices", [])

                        delta_content: str | None = None
                        delta_tool_calls: list[dict] | None = None
                        finish_reason: str | None = None

                        if choices:
                            delta = choices[0].get("delta", {})
                            delta_content = delta.get("content")
                            delta_tool_calls = delta.get("tool_calls")
                            finish_reason = choices[0].get("finish_reason")

                        # usage on final chunk (stream_options)
                        usage: TokenUsage | None = None
                        if "usage" in chunk_data and chunk_data["usage"]:
                            u = chunk_data["usage"]
                            usage = TokenUsage(
                                prompt_tokens=u.get("prompt_tokens", 0),
                                completion_tokens=u.get("completion_tokens", 0),
                                total_tokens=u.get("total_tokens", 0),
                            )

                        yield StreamChunk(
                            id=chunk_id,
                            model=chunk_model,
                            delta_content=delta_content,
                            delta_tool_calls=delta_tool_calls,
                            finish_reason=_map_finish_reason(finish_reason)
                            if finish_reason
                            else None,
                            usage=usage,
                        )
            except httpx.TimeoutException as exc:
                raise self.normalize_error(exc)
            except httpx.RequestError as exc:
                raise self.normalize_error(exc)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        start = time.monotonic()
        try:
            async with self._build_client(timeout=10.0) as client:
                resp = await client.get("/models")
            latency_ms = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return {"healthy": True, "latency_ms": latency_ms, "detail": "ok"}
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "detail": f"HTTP {resp.status_code}",
            }
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "detail": str(exc),
            }

    # ------------------------------------------------------------------
    # Error normalisation
    # ------------------------------------------------------------------

    def normalize_error(self, exc: Exception) -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        if isinstance(exc, httpx.TimeoutException):
            return ProviderError(
                "Request timed out",
                status_code=504,
                error_code="timeout",
                retryable=True,
                provider=self.provider_type,
            )
        if isinstance(exc, httpx.ConnectError):
            return ProviderError(
                f"Connection error: {exc}",
                status_code=503,
                error_code="connection_error",
                retryable=True,
                provider=self.provider_type,
            )
        if isinstance(exc, httpx.RequestError):
            return ProviderError(
                f"Request error: {exc}",
                status_code=502,
                error_code="request_error",
                retryable=True,
                provider=self.provider_type,
            )
        return ProviderError(
            str(exc),
            status_code=500,
            error_code="internal_error",
            retryable=False,
            provider=self.provider_type,
        )

    def _raise_from_response(self, resp: httpx.Response) -> ProviderError:
        try:
            data = resp.json()
            err_obj = data.get("error", {})
            message = err_obj.get("message", resp.text)
            error_code = err_obj.get("code") or err_obj.get("type") or "provider_error"
        except Exception:
            message = resp.text
            error_code = "provider_error"

        return self._map_status_to_error(resp.status_code, message, error_code)

    def _raise_from_bytes(
        self, status_code: int, body: bytes
    ) -> ProviderError:
        try:
            data = json.loads(body)
            err_obj = data.get("error", {})
            message = err_obj.get("message", body.decode())
            error_code = err_obj.get("code") or err_obj.get("type") or "provider_error"
        except Exception:
            message = body.decode(errors="replace")
            error_code = "provider_error"

        return self._map_status_to_error(status_code, message, error_code)

    def _map_status_to_error(
        self, status_code: int, message: str, error_code: str
    ) -> ProviderError:
        retryable = status_code in {429, 500, 502, 503, 504}
        if status_code == 401:
            error_code = "auth_error"
        elif status_code == 429:
            error_code = "rate_limit"
        elif status_code == 400:
            error_code = "validation_error"

        return ProviderError(
            message,
            status_code=status_code,
            error_code=error_code,
            retryable=retryable,
            provider=self.provider_type,
        )

    # ------------------------------------------------------------------
    # Token estimation
    # ------------------------------------------------------------------

    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        try:
            enc = _get_encoding("gpt-4o")
            total = 0
            for m in messages:
                total += 4  # role + separator overhead
                content = m.content if isinstance(m.content, str) else str(m.content)
                total += len(enc.encode(content))
            total += 2  # reply priming
            return total
        except Exception:
            # Fallback: rough word count
            total = 0
            for m in messages:
                content = m.content if isinstance(m.content, str) else str(m.content)
                total += max(1, len(content.split()) * 4 // 3)
            return total
