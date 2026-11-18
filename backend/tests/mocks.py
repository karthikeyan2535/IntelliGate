"""
Deterministic mock LLM provider for automated test suite.
Implements the full BaseProvider interface with instant response and streaming capabilities.
"""
from __future__ import annotations

import time
import uuid
from typing import AsyncIterator

from app.providers.base import (
    BaseProvider,
    ProviderError,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    StreamChunk,
    TokenUsage,
)


class MockLLMProvider(BaseProvider):
    provider_type = "mock"

    def __init__(self, name: str = "mock"):
        self.name = name

    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        content = "IntelliGate mock response: Quantum computing leverages superposition and entanglement to perform complex computations."
        prompt_tokens = self.estimate_tokens(request.messages)
        completion_tokens = 18

        return ProviderResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model=request.model,
            content=content,
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def stream_completion(self, request: ProviderRequest) -> AsyncIterator[StreamChunk]:
        words = ["Quantum", " computing", " leverages", " quantum", " physics", " principles."]
        req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        for idx, w in enumerate(words):
            finish = "stop" if idx == len(words) - 1 else None
            usage = TokenUsage(prompt_tokens=10, completion_tokens=len(words), total_tokens=10 + len(words)) if finish else None
            yield StreamChunk(
                id=req_id,
                model=request.model,
                delta_content=w,
                finish_reason=finish,
                usage=usage,
            )

    async def health_check(self) -> dict:
        return {"status": "healthy", "latency_ms": 5}

    def normalize_error(self, exc: Exception) -> ProviderError:
        return ProviderError(message=str(exc), status_code=500)

    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        return sum(len(str(m.content).split()) * 2 for m in messages)

