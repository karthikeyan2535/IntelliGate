"""
Google Gemini provider adapter for IntelliGate.

Uses the Generative Language REST API directly.
Reference: https://ai.google.dev/api/generate-content
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

GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


def _translate_role(role: str) -> str:
    """Map canonical roles to Gemini roles (user / model)."""
    if role == "assistant":
        return "model"
    if role in {"user", "tool", "function"}:
        return "user"
    return "user"


def _translate_messages(
    messages: list[ProviderMessage],
) -> tuple[str | None, list[dict]]:
    """
    Convert messages to Gemini contents format.
    Returns (system_instruction, contents).
    """
    system_instruction: str | None = None
    contents: list[dict] = []

    for m in messages:
        if m.role == "system":
            if isinstance(m.content, str):
                system_instruction = m.content
            else:
                system_instruction = " ".join(
                    b.get("text", "") if isinstance(b, dict) else str(b)
                    for b in m.content
                )
            continue

        gemini_role = _translate_role(m.role)
        if isinstance(m.content, str):
            parts = [{"text": m.content}]
        elif isinstance(m.content, list):
            parts = []
            for block in m.content:
                if isinstance(block, str):
                    parts.append({"text": block})
                elif isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append({"text": block.get("text", "")})
                    elif block.get("type") == "image_url":
                        # inline_data for base64 images
                        url = block.get("image_url", {}).get("url", "")
                        if url.startswith("data:"):
                            mime, b64 = url[5:].split(",", 1)
                            mime = mime.split(";")[0]
                            parts.append(
                                {"inline_data": {"mime_type": mime, "data": b64}}
                            )
                        else:
                            parts.append({"text": f"[image: {url}]"})
                    else:
                        parts.append({"text": str(block)})
        else:
            parts = [{"text": str(m.content)}]

        contents.append({"role": gemini_role, "parts": parts})

    return system_instruction, contents


def _extract_text(candidate: dict) -> str | None:
    """Extract text from a Gemini candidate."""
    parts = candidate.get("content", {}).get("parts", [])
    texts = [p.get("text", "") for p in parts if "text" in p]
    return "".join(texts) or None


def _map_finish_reason(reason: str | None) -> str:
    mapping = {
        "STOP": "stop",
        "MAX_TOKENS": "length",
        "SAFETY": "content_filter",
        "RECITATION": "content_filter",
        "TOOL_CODE": "tool_calls",
        "OTHER": "stop",
        "FINISH_REASON_UNSPECIFIED": "stop",
    }
    return mapping.get(reason or "", "stop")


class GeminiProvider(BaseProvider):
    """Google Gemini provider adapter."""

    provider_type = "gemini"

    def __init__(
        self,
        api_key: str,
        base_url: str = GEMINI_API_BASE,
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
            timeout=httpx.Timeout(timeout or self._timeout),
        )

    # ------------------------------------------------------------------
    # Payload builder
    # ------------------------------------------------------------------

    def _build_payload(self, request: ProviderRequest) -> dict[str, Any]:
        system_instruction, contents = _translate_messages(request.messages)

        payload: dict[str, Any] = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        generation_config: dict[str, Any] = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.top_p is not None:
            generation_config["topP"] = request.top_p
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        if request.stop:
            generation_config["stopSequences"] = request.stop
        if request.response_format:
            fmt = request.response_format.get("type")
            if fmt == "json_object":
                generation_config["responseMimeType"] = "application/json"

        if generation_config:
            payload["generationConfig"] = generation_config

        if request.tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.parameters,
                        }
                        for t in request.tools
                    ]
                }
            ]

        payload.update(request.extra_params)
        return payload

    def _model_url_part(self, model: str) -> str:
        """Return model name, adding gemini- prefix if needed."""
        if not model.startswith("models/"):
            return model
        return model  # already prefixed

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------

    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        payload = self._build_payload(request)
        model = self._model_url_part(request.model)
        url = f"/v1beta/models/{model}:generateContent"
        params = {"key": self._api_key}

        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("gemini.chat_completion.start")

        async with self._build_client() as client:
            try:
                resp = await client.post(url, json=payload, params=params)
            except httpx.TimeoutException as exc:
                raise self.normalize_error(exc)
            except httpx.RequestError as exc:
                raise self.normalize_error(exc)

        if resp.status_code != 200:
            raise self._raise_from_response(resp)

        data: dict = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ProviderError(
                "No candidates in Gemini response",
                status_code=502,
                error_code="no_candidates",
                retryable=False,
                provider=self.provider_type,
            )

        candidate = candidates[0]
        content = _extract_text(candidate)
        finish_reason = _map_finish_reason(candidate.get("finishReason"))

        # Tool calls
        tool_calls: list[dict] | None = None
        parts = candidate.get("content", {}).get("parts", [])
        fc_parts = [p for p in parts if "functionCall" in p]
        if fc_parts:
            tool_calls = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": p["functionCall"]["name"],
                        "arguments": json.dumps(p["functionCall"].get("args", {})),
                    },
                }
                for i, p in enumerate(fc_parts)
            ]

        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        return ProviderResponse(
            id=data.get("responseId", f"gemini-{int(time.time())}"),
            model=request.model,
            content=content,
            finish_reason=finish_reason,
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
        payload = self._build_payload(request)
        model = self._model_url_part(request.model)
        url = f"/v1beta/models/{model}:streamGenerateContent"
        params = {"key": self._api_key, "alt": "sse"}

        log = logger.bind(provider=self.provider_type, model=request.model)
        log.debug("gemini.stream_completion.start")

        chunk_id = f"gemini-{int(time.time())}"

        async with self._build_client() as client:
            try:
                async with client.stream(
                    "POST", url, json=payload, params=params
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise self._raise_from_bytes(resp.status_code, body)

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue

                        raw = line[6:]
                        try:
                            evt_data = json.loads(raw)
                        except json.JSONDecodeError:
                            log.warning("gemini.stream.bad_json", raw=raw)
                            continue

                        candidates = evt_data.get("candidates", [])
                        if not candidates:
                            continue

                        candidate = candidates[0]
                        finish_reason_raw = candidate.get("finishReason")
                        finish_reason = (
                            _map_finish_reason(finish_reason_raw)
                            if finish_reason_raw
                            else None
                        )

                        # Extract text delta
                        parts = candidate.get("content", {}).get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if "text" in p]
                        delta_content = "".join(text_parts) or None

                        # Usage on final chunk
                        usage: TokenUsage | None = None
                        usage_meta = evt_data.get("usageMetadata", {})
                        if usage_meta and finish_reason:
                            pt = usage_meta.get("promptTokenCount", 0)
                            ct = usage_meta.get("candidatesTokenCount", 0)
                            usage = TokenUsage(
                                prompt_tokens=pt,
                                completion_tokens=ct,
                                total_tokens=pt + ct,
                            )

                        yield StreamChunk(
                            id=chunk_id,
                            model=request.model,
                            delta_content=delta_content,
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
                resp = await client.get(
                    "/v1beta/models", params={"key": self._api_key}
                )
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
            error_code = err.get("status", "PROVIDER_ERROR").lower()
        except Exception:
            message = resp.text
            error_code = "provider_error"
        return self._map_status_to_error(resp.status_code, message, error_code)

    def _raise_from_bytes(self, status_code: int, body: bytes) -> ProviderError:
        try:
            data = json.loads(body)
            err = data.get("error", {})
            message = err.get("message", body.decode())
            error_code = err.get("status", "PROVIDER_ERROR").lower()
        except Exception:
            message = body.decode(errors="replace")
            error_code = "provider_error"
        return self._map_status_to_error(status_code, message, error_code)

    def _map_status_to_error(
        self, status_code: int, message: str, error_code: str
    ) -> ProviderError:
        retryable = status_code in {429, 500, 502, 503, 504}
        if status_code == 400:
            error_code = "validation_error"
        elif status_code == 401 or status_code == 403:
            error_code = "auth_error"
        elif status_code == 429:
            error_code = "rate_limit"
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
        total = 0
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            total += max(1, int(len(content.split()) * 1.33))
            total += 3
        return total + 2
