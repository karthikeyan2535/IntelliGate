"""
Organization and project schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import Field, field_validator

from app.database.models import OrgRole
from app.schemas.common import ORMBase


# ── Organization ──────────────────────────────────────────────────────────────


class OrgCreateRequest(ORMBase):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)


class OrgUpdateRequest(ORMBase):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class OrgResponse(ORMBase):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrgMemberResponse(ORMBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgRole
    created_at: datetime


class InviteMemberRequest(ORMBase):
    user_id: uuid.UUID
    role: OrgRole = OrgRole.MEMBER


# ── Project ───────────────────────────────────────────────────────────────────


class ProjectCreateRequest(ORMBase):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)


class ProjectUpdateRequest(ORMBase):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class ProjectResponse(ORMBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
