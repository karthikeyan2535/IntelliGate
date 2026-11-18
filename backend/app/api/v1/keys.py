"""
Virtual API Key management API.
Allows organizations and projects to issue scoped virtual keys with rate limits and model restrictions.
The raw secret key is displayed exactly once upon creation and only an HMAC-SHA256 hash is persisted.
"""
from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.security import generate_api_key
from app.database.base import get_db
from app.database.models import KeyStatus, Project, User, VirtualApiKey
from app.schemas.keys import (
    KeyCreateRequest,
    KeyCreateResponse,
    KeyResponse,
    KeyUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Virtual API Keys"])


@router.post(
    "/projects/{project_id}/keys",
    response_model=KeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Virtual API Key",
)
async def create_key(
    project_id: uuid.UUID,
    payload: KeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a secure virtual API key with prefix 'ig-'.
    Returns the raw secret key ONCE. The raw key is never stored in the database.
    """
    # Verify project exists
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_key, key_hash, prefix = generate_api_key()

    new_key = VirtualApiKey(
        project_id=project_id,
        name=payload.name,
        key_prefix=prefix,
        key_hash=key_hash,
        status=KeyStatus.ACTIVE,
        expires_at=payload.expires_at,
        allowed_models=payload.allowed_models or [],
        rate_limit_rpm=payload.rate_limit_rpm,
        rate_limit_tpm=payload.rate_limit_tpm,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    logger.info("Created Virtual API Key", key_id=str(new_key.id), project_id=str(project_id))

    return KeyCreateResponse(
        id=new_key.id,
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        raw_key=raw_key,
        status=new_key.status,
        created_at=new_key.created_at,
    )


@router.get(
    "/projects/{project_id}/keys",
    response_model=List[KeyResponse],
    summary="List all keys for a project",
)
async def list_keys(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(VirtualApiKey).where(VirtualApiKey.project_id == project_id).order_by(VirtualApiKey.created_at.desc())
    res = await db.execute(stmt)
    keys = res.scalars().all()
    return keys


@router.get(
    "/keys/{key_id}",
    response_model=KeyResponse,
    summary="Get details for a virtual key",
)
async def get_key_details(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(VirtualApiKey).where(VirtualApiKey.id == key_id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.patch(
    "/keys/{key_id}",
    response_model=KeyResponse,
    summary="Update virtual key settings",
)
async def update_key(
    key_id: uuid.UUID,
    payload: KeyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(VirtualApiKey).where(VirtualApiKey.id == key_id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    if payload.name is not None:
        key.name = payload.name
    if payload.expires_at is not None:
        key.expires_at = payload.expires_at
    if payload.allowed_models is not None:
        key.allowed_models = payload.allowed_models
    if payload.rate_limit_rpm is not None:
        key.rate_limit_rpm = payload.rate_limit_rpm
    if payload.rate_limit_tpm is not None:
        key.rate_limit_tpm = payload.rate_limit_tpm

    await db.commit()
    await db.refresh(key)
    return key


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a virtual API key",
)
async def revoke_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(VirtualApiKey).where(VirtualApiKey.id == key_id)
    res = await db.execute(stmt)
    key = res.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    key.status = KeyStatus.REVOKED
    await db.commit()
    logger.info("Revoked Virtual API Key", key_id=str(key_id))
    return None

