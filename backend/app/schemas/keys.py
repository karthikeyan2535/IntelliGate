"""
Virtual API key schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from app.database.models import KeyStatus
from app.schemas.common import ORMBase


class KeyCreateRequest(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    expires_at: Optional[datetime] = None
    allowed_models: Optional[list[str]] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=100_000)
    rate_limit_tpm: Optional[int] = Field(None, ge=1, le=10_000_000)


class KeyUpdateRequest(ORMBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    expires_at: Optional[datetime] = None
    allowed_models: Optional[list[str]] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=100_000)
    rate_limit_tpm: Optional[int] = Field(None, ge=1, le=10_000_000)


class KeyCreateResponse(ORMBase):
    """Returned only on creation — raw key shown once."""
    id: uuid.UUID
    name: str
    key_prefix: str
    raw_key: str   # shown once, never stored in plaintext
    status: KeyStatus
    created_at: datetime


class KeyResponse(ORMBase):
    """Standard response — never includes raw key."""
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    key_prefix: str
    status: KeyStatus
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    allowed_models: Optional[list[str]] = None
    rate_limit_rpm: Optional[int] = None
    rate_limit_tpm: Optional[int] = None
    created_at: datetime
    updated_at: datetime
