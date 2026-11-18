"""
OpenAI-compatible gateway request/response schemas.

These are the public-facing schemas for the /v1/chat/completions endpoint.
They mirror the OpenAI API format so existing clients work without modification.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    model_config = ConfigDict(populate_by_name=True)

    role: Literal["system", "user", "assistant", "tool", "function"]
    content: str | list | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request with gateway extensions."""

    model_config = ConfigDict(populate_by_name=True)

    # Core OpenAI fields
    model: str
    messages: list[ChatMessage] = Field(..., min_length=1)
    temperature: float | None = Field(None, ge=0, le=2)
    top_p: float | None = Field(None, ge=0, le=1)
    max_tokens: int | None = Field(None, gt=0)
    stop: str | list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None
    n: int | None = Field(None, ge=1, le=10)
    presence_penalty: float | None = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0)
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    seed: int | None = None

    # Gateway extensions (may appear in body or be forwarded from headers)
    x_routing_policy: str | None = Field(None, alias="x-routing-policy")
    x_cache_ttl: int | None = Field(None, alias="x-cache-ttl")
    x_fallback_model: str | None = Field(None, alias="x-fallback-model")
    x_override_category: str | None = Field(None, alias="x-override-category")
    x_override_complexity: str | None = Field(None, alias="x-override-complexity")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ChatCompletionMessage(BaseModel):
    """Message in a completion response."""

    role: str = "assistant"
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    function_call: dict[str, Any] | None = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChatCompletionMessage
    finish_reason: str
    logprobs: dict[str, Any] | None = None


class ChatCompletionUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    # Extended fields (may not always be present)
    prompt_tokens_details: dict[str, Any] | None = None
    completion_tokens_details: dict[str, Any] | None = None


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible non-streaming response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = None
    system_fingerprint: str | None = None

    # IntelliGate extension headers (populated as response metadata)
    # Not serialized in JSON body — added as response headers by the endpoint.


# ---------------------------------------------------------------------------
# Streaming chunks
# ---------------------------------------------------------------------------


class ChatCompletionDelta(BaseModel):
    """Delta content in a streaming chunk."""

    role: str | None = None
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionChunkChoice(BaseModel):
    """A choice in a streaming chunk."""

    index: int
    delta: ChatCompletionDelta
    finish_reason: str | None = None
    logprobs: dict[str, Any] | None = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]
    usage: ChatCompletionUsage | None = None
    system_fingerprint: str | None = None


# ---------------------------------------------------------------------------
# Models list
# ---------------------------------------------------------------------------


class ModelObject(BaseModel):
    """An entry in the /v1/models response."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "intelligate"


class ModelsListResponse(BaseModel):
    """Response from GET /v1/models."""

    object: str = "list"
    data: list[ModelObject]


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response envelope."""

    error: ErrorDetail
