"""
Base provider abstractions for IntelliGate.

All provider adapters must implement BaseProvider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, AsyncIterator


@dataclass
class ProviderMessage:
    """A single message in a conversation."""

    role: str  # system / user / assistant / tool
    content: str | list  # list for multimodal content blocks

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant", "tool", "function"}:
            raise ValueError(f"Invalid role: {self.role!r}")


@dataclass
class ProviderTool:
    """A tool/function definition."""

    name: str
    description: str
    parameters: dict  # JSON Schema object


@dataclass
class ProviderRequest:
    """Canonical provider-agnostic request."""

    model: str
    messages: list[ProviderMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None
    tools: list[ProviderTool] | None = None
    tool_choice: str | dict | None = None
    response_format: dict | None = None
    stream: bool = False
    extra_params: dict = field(default_factory=dict)


@dataclass
class TokenUsage:
    """Token accounting."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class ProviderResponse:
    """Canonical provider response (non-streaming)."""

    id: str
    model: str
    content: str | None
    finish_reason: str  # stop / length / tool_calls / content_filter
    tool_calls: list[dict] | None = None
    usage: TokenUsage | None = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""

    id: str
    model: str
    delta_content: str | None = None
    delta_tool_calls: list[dict] | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None  # only on final chunk


class ProviderError(Exception):
    """Raised by provider adapters to signal structured errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "provider_error",
        retryable: bool = False,
        provider: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.retryable = retryable
        self.provider = provider
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"ProviderError(status={self.status_code}, code={self.error_code!r}, "
            f"retryable={self.retryable}, msg={self.message!r})"
        )


class BaseProvider(ABC):
    """Abstract base class every provider adapter must implement."""

    provider_type: str  # e.g. "openai", "anthropic", "gemini"

    # ------------------------------------------------------------------
    # Core request methods
    # ------------------------------------------------------------------

    @abstractmethod
    async def chat_completion(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a non-streaming chat completion."""
        ...

    @abstractmethod
    async def stream_completion(
        self, request: ProviderRequest
    ) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat completion, yielding chunks."""
        ...

    # ------------------------------------------------------------------
    # Operational
    # ------------------------------------------------------------------

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Return health status dict: {healthy: bool, latency_ms: float, detail: str}."""
        ...

    @abstractmethod
    def normalize_error(self, exc: Exception) -> ProviderError:
        """Translate any raw exception into a structured ProviderError."""
        ...

    @abstractmethod
    def estimate_tokens(self, messages: list[ProviderMessage]) -> int:
        """Fast local token count estimate (no API call)."""
        ...
