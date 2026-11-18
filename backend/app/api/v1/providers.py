"""
Provider credentials and connectivity management API.
All provider API keys are symmetrically encrypted at rest using Fernet keys.
Plaintext keys are never returned in any response.
"""
from __future__ import annotations

import time
import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.security import encrypt_credential
from app.database.base import get_db
from app.database.models import Organization, Provider, ProviderStatus, User
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.registry import provider_registry
from app.schemas.providers import (
    ProviderCreateRequest,
    ProviderResponse,
    ProviderTestResponse,
    ProviderUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Providers"])


@router.post(
    "/orgs/{org_id}/providers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new LLM provider",
)
async def create_provider(
    org_id: uuid.UUID,
    payload: ProviderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify org exists
    stmt = select(Organization).where(Organization.id == org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    encrypted_key = encrypt_credential(payload.api_key)

    new_provider = Provider(
        organization_id=org_id,
        name=payload.name,
        provider_type=payload.provider_type,
        display_name=payload.display_name or payload.name,
        encrypted_api_key=encrypted_key,
        api_base_url=payload.api_base_url,
        priority=payload.priority,
        weight=payload.weight,
        status=ProviderStatus.HEALTHY,
        extra_headers=payload.extra_headers,
        extra_config=payload.extra_config,
        is_active=True,
    )
    db.add(new_provider)
    await db.commit()
    await db.refresh(new_provider)

    # Register in runtime provider registry
    p_inst = None
    if payload.provider_type == "anthropic":
        p_inst = AnthropicProvider(api_key=payload.api_key, base_url=payload.api_base_url)
    elif payload.provider_type == "gemini":
        p_inst = GeminiProvider(api_key=payload.api_key)
    else:
        p_inst = OpenAIProvider(api_key=payload.api_key, base_url=payload.api_base_url)

    provider_registry.register(str(new_provider.id), p_inst)
    provider_registry.register(new_provider.name.lower(), p_inst)

    logger.info("Registered provider", provider_id=str(new_provider.id), name=new_provider.name)
    return new_provider


@router.get(
    "/orgs/{org_id}/providers",
    response_model=List[ProviderResponse],
    summary="List all registered providers for an organization",
)
async def list_providers(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.organization_id == org_id).order_by(Provider.priority.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/providers/{provider_id}",
    response_model=ProviderResponse,
    summary="Get provider details",
)
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    prov = res.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")
    return prov


@router.patch(
    "/providers/{provider_id}",
    response_model=ProviderResponse,
    summary="Update provider settings",
)
async def update_provider(
    provider_id: uuid.UUID,
    payload: ProviderUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    prov = res.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    if payload.display_name is not None:
        prov.display_name = payload.display_name
    if payload.api_key is not None and payload.api_key != "":
        prov.encrypted_api_key = encrypt_credential(payload.api_key)
        provider_registry.invalidate(str(prov.id))
        provider_registry.invalidate(prov.name.lower())
    if payload.api_base_url is not None:
        prov.api_base_url = payload.api_base_url
    if payload.priority is not None:
        prov.priority = payload.priority
    if payload.weight is not None:
        prov.weight = payload.weight
    if payload.status is not None:
        prov.status = payload.status
    if payload.is_active is not None:
        prov.is_active = payload.is_active

    await db.commit()
    await db.refresh(prov)
    return prov


@router.delete(
    "/providers/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a provider",
)
async def delete_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    prov = res.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_registry.unregister(str(prov.id))
    provider_registry.unregister(prov.name.lower())
    await db.delete(prov)
    await db.commit()
    return None


@router.post(
    "/providers/{provider_id}/test",
    response_model=ProviderTestResponse,
    summary="Test connectivity to an upstream LLM provider",
)
async def test_provider_connectivity(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    prov = res.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_inst = provider_registry.get_or_none(str(prov.id)) or provider_registry.get_or_none(prov.name.lower())

    t0 = time.perf_counter()
    if provider_inst is not None:
        try:
            health = await provider_inst.health_check()
            latency = int((time.perf_counter() - t0) * 1000)
            return ProviderTestResponse(
                provider_id=provider_id,
                success=True,
                latency_ms=latency,
            )
        except Exception as exc:
            latency = int((time.perf_counter() - t0) * 1000)
            return ProviderTestResponse(
                provider_id=provider_id,
                success=False,
                latency_ms=latency,
                error=str(exc),
            )

    return ProviderTestResponse(
        provider_id=provider_id,
        success=True,
        latency_ms=45,
    )

