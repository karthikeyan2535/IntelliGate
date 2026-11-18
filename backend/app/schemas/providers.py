"""
Provider and model schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import Field, field_validator

from app.database.models import ProviderStatus
from app.schemas.common import ORMBase


# ── Provider ──────────────────────────────────────────────────────────────────


class ProviderCreateRequest(ORMBase):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=255)
    api_key: str = Field(..., min_length=1)        # plaintext — encrypted on write
    api_base_url: Optional[str] = Field(None, max_length=512)
    priority: int = Field(100, ge=1, le=1000)
    weight: int = Field(1, ge=1, le=100)
    extra_headers: Optional[dict[str, str]] = None
    extra_config: Optional[dict[str, Any]] = None


class ProviderUpdateRequest(ORMBase):
    display_name: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = None                  # if provided, re-encrypt
    api_base_url: Optional[str] = Field(None, max_length=512)
    priority: Optional[int] = Field(None, ge=1, le=1000)
    weight: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[ProviderStatus] = None
    extra_headers: Optional[dict[str, str]] = None
    extra_config: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProviderResponse(ORMBase):
    """Never returns decrypted key."""
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    provider_type: str
    display_name: Optional[str] = None
    api_base_url: Optional[str] = None
    status: ProviderStatus
    priority: int
    weight: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderTestResponse(ORMBase):
    provider_id: uuid.UUID
    success: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None


# ── LLM Model ─────────────────────────────────────────────────────────────────


class ModelCreateRequest(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    aliases: Optional[list[str]] = None
    context_window: Optional[int] = Field(None, ge=1)
    max_output_tokens: Optional[int] = Field(None, ge=1)
    input_cost_per_1k_tokens: Optional[Decimal] = None
    output_cost_per_1k_tokens: Optional[Decimal] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    extra_params: Optional[dict[str, Any]] = None


class ModelUpdateRequest(ORMBase):
    display_name: Optional[str] = Field(None, max_length=255)
    aliases: Optional[list[str]] = None
    context_window: Optional[int] = Field(None, ge=1)
    max_output_tokens: Optional[int] = Field(None, ge=1)
    input_cost_per_1k_tokens: Optional[Decimal] = None
    output_cost_per_1k_tokens: Optional[Decimal] = None
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    is_active: Optional[bool] = None
    extra_params: Optional[dict[str, Any]] = None


class ModelResponse(ORMBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    name: str
    display_name: Optional[str] = None
    aliases: Optional[list[str]] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_cost_per_1k_tokens: Optional[Decimal] = None
    output_cost_per_1k_tokens: Optional[Decimal] = None
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
