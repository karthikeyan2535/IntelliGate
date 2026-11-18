"""
Anthropic Claude provider adapter for IntelliGate.

Translates between IntelliGate's canonical format and Anthropic's Messages API.
Reference: https://docs.anthropic.com/en/api/messages
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

ANTHROPIC_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


def _translate_finish_reason(stop_reason: str | None) -> str:
    """Map Anthropic stop reasons to canonical finish_reason."""
    mapping = {
        "end_turn": "stop",
        "max_tokens": "length",
        "tool_use": "tool_calls",
        "stop_sequence": "stop",
    }
    return mapping.get(stop_reason or "", "stop")


def _translate_messages(
    messages: list[ProviderMessage],
) -> tuple[str | None, list[dict]]:
    """
    Split messages into (system_prompt, anthropic_messages).
    Anthropic requires system as a top-level field, not in messages.
    """
    system_prompt: str | None = None
    anthropic_messages: list[dict] = []

    for m in messages:
        if m.role == "system":
            if isinstance(m.content, str):
                system_prompt = m.content
            else:
                # list of content blocks → join text parts
                system_prompt = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in m.content
                )
            continue

        if m.role == "tool":
            # Tool results go as user messages with tool_result content
            anthropic_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": getattr(m, "tool_call_id", ""),
                            "content": m.content
                            if isinstance(m.content, str)
                            else m.content,
                        }
                    ],
                }
            )
            continue

        # user / assistant
        role = "user" if m.role == "user" else "assistant"
        if isinstance(m.content, str):
            content: Any = m.content
        else:
            content = m.content  # already a list of blocks

        anthropic_messages.append({"role": role, "content": content})

    return system_prompt, anthropic_messages


def _extract_content_and_tools(
    content_blocks: list[dict],
) -> tuple[str | None, list[dict] | None]:
    """Extract text content and tool_use blocks from Anthropic content array."""
    text_parts: list[str] = []
    tool_calls: list[dict] = []

    for block in content_blocks:
        btype = block.get("type")
        if btype == "text":
            text_parts.append(block.get("text", ""))
        elif btype == "tool_use":
            tool_calls.append(
                {
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": json.dumps(block.get("input", {})),
                    },
                }
            )

    return (" ".join(text_parts) or None), (tool_calls if tool_calls else None)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider adapter."""

    provider_type = "anthropic"

    def __init__(
        self,
        api_key: str,
        base_url: str = ANTHROPIC_API_BASE,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    # ------------------------------------------------------------------
    # HTTP client
    # ------------------------------------------------------------------

    def _build_client(self, timeout: float | None = None) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout or self._timeout),
        )

    # ------------------------------------------------------------------
    # Payload builder
    # ------------------------------------------------------------------

    def _build_payload(
        self, request: ProviderRequest, stream: bool = False
    ) -> dict[str, Any]:
        system_prompt, messages = _translate_messages(request.messages)

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "stream": stream,
        }

        if system_prompt:
            payload["system"] = system_prompt
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        else:
            payload["max_tokens"] = 4096  # Anthropic requires max_tokens

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.stop:
            payload["stop_sequences"] = request.stop
        if request.tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in request.tools
            ]
        if request.tool_choice is not None:
            if isinstance(request.tool_choice, str):
                payload["tool_choice"] = {"type": request.tool_choice}
            else:
                payload["tool_choice"] = request.tool_choice

        payload.update(request.extra_params)
        return payload

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------

    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        payload = self._build_payload(request, stream=False)
        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("anthropic.chat_completion.start")

        async with self._build_client() as client:
            try:
                resp = await client.post("/v1/messages", json=payload)
            except httpx.TimeoutException as exc:
                raise self.normalize_error(exc)
            except httpx.RequestError as exc:
                raise self.normalize_error(exc)

        if resp.status_code != 200:
            raise self._raise_from_response(resp)

        data: dict = resp.json()
        content_blocks = data.get("content", [])
        content, tool_calls = _extract_content_and_tools(content_blocks)

        usage_data = data.get("usage", {})
        prompt_tokens = usage_data.get("input_tokens", 0)
        completion_tokens = usage_data.get("output_tokens", 0)
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        return ProviderResponse(
            id=data.get("id", ""),
            model=data.get("model", request.model),
            content=content,
            finish_reason=_translate_finish_reason(data.get("stop_reason")),
            tool_calls=tool_calls,
            usage=usage,
            raw_response=data,
        )

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream_completion(
        self, request: ProviderRequest
    ) -> AsyncIterator[StreamChunk]:
        payload = self._build_payload(request, stream=True)
        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("anthropic.stream_completion.start")

        chunk_id: str = ""
        chunk_model: str = request.model
        # accumulate tool_use blocks during stream
        tool_use_blocks: dict[int, dict] = {}

        async with self._build_client() as client:
            try:
                async with client.stream(
                    "POST", "/v1/messages", json=payload
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise self._raise_from_bytes(resp.status_code, body)

                    event_type: str = ""
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event: "):
                            event_type = line[7:]
                            continue

                        if not line.startswith("data: "):
                            continue

                        raw = line[6:]
                        try:
                            evt_data = json.loads(raw)
                        except json.JSONDecodeError:
                            log.warning("anthropic.stream.bad_json", raw=raw)
                            continue

                        # message_start → grab id and model
                        if event_type == "message_start":
                            msg = evt_data.get("message", {})
                            chunk_id = msg.get("id", "")
                            chunk_model = msg.get("model", request.model)

                        elif event_type == "content_block_start":
                            block = evt_data.get("content_block", {})
                            idx = evt_data.get("index", 0)
                            if block.get("type") == "tool_use":
                                tool_use_blocks[idx] = {
                                    "id": block.get("id"),
                                    "name": block.get("name"),
                                    "input_json": "",
                                }

                        elif event_type == "content_block_delta":
                            delta = evt_data.get("delta", {})
                            idx = evt_data.get("index", 0)
                            dtype = delta.get("type")

                            if dtype == "text_delta":
                                yield StreamChunk(
                                    id=chunk_id,
                                    model=chunk_model,
                                    delta_content=delta.get("text", ""),
                                )

                            elif dtype == "input_json_delta":
                                if idx in tool_use_blocks:
                                    tool_use_blocks[idx]["input_json"] += delta.get(
                                        "partial_json", ""
                                    )

                        elif event_type == "message_delta":
                            delta = evt_data.get("delta", {})
                            usage_data = evt_data.get("usage", {})
                            stop_reason = delta.get("stop_reason")
                            finish_reason = _translate_finish_reason(stop_reason)

                            # Emit any accumulated tool calls
                            tool_calls: list[dict] | None = None
                            if tool_use_blocks:
                                tool_calls = []
                                for blk in tool_use_blocks.values():
                                    try:
                                        input_data = json.loads(blk["input_json"] or "{}")
                                    except Exception:
                                        input_data = {}
                                    tool_calls.append(
                                        {
                                            "id": blk["id"],
                                            "type": "function",
                                            "function": {
                                                "name": blk["name"],
                                                "arguments": json.dumps(input_data),
                                            },
                                        }
                                    )

                            usage: TokenUsage | None = None
                            if usage_data:
                                output_tokens = usage_data.get("output_tokens", 0)
                                # input tokens come from message_start
                                usage = TokenUsage(
                                    prompt_tokens=0,
                                    completion_tokens=output_tokens,
                                    total_tokens=output_tokens,
                                )

                            yield StreamChunk(
                                id=chunk_id,
                                model=chunk_model,
                                delta_tool_calls=tool_calls,
                                finish_reason=finish_reason,
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
                resp = await client.get("/v1/models")
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
            return {"healthy": False, "latency_ms": latency_ms, "detail": str(exc)}

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
            str(exc), status_code=500, error_code="internal_error", retryable=False,
            provider=self.provider_type,
        )

    def _raise_from_response(self, resp: httpx.Response) -> ProviderError:
        try:
            data = resp.json()
            err = data.get("error", {})
            message = err.get("message", resp.text)
            error_code = err.get("type", "provider_error")
        except Exception:
            message = resp.text
            error_code = "provider_error"
        return self._map_status_to_error(resp.status_code, message, error_code)

    def _raise_from_bytes(self, status_code: int, body: bytes) -> ProviderError:
        try:
            data = json.loads(body)
            err = data.get("error", {})
            message = err.get("message", body.decode())
            error_code = err.get("type", "provider_error")
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
    # Token estimation (word-based for Anthropic)
    # ------------------------------------------------------------------

    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        total = 0
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            # ~1.33 tokens per word is a reasonable approximation
            total += max(1, int(len(content.split()) * 1.33))
            total += 4  # role overhead
        return total + 2
