"""
Model Registration and Configuration API.
Allows registering LLM models for specific providers, configuring aliases (e.g. fast-model, balanced-model),
and defining custom token pricing rates.
"""
from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database.base import get_db
from app.database.models import LLMModel, Provider, User
from app.schemas.providers import (
    ModelCreateRequest,
    ModelResponse,
    ModelUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Models"])


@router.post(
    "/providers/{provider_id}/models",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new LLM model for a provider",
)
async def create_model(
    provider_id: uuid.UUID,
    payload: ModelCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Provider).where(Provider.id == provider_id)
    res = await db.execute(stmt)
    prov = res.scalar_one_or_none()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found")

    new_model = LLMModel(
        provider_id=provider_id,
        name=payload.name,
        display_name=payload.display_name or payload.name,
        aliases=payload.aliases or [],
        context_window=payload.context_window,
        max_output_tokens=payload.max_output_tokens,
        input_cost_per_1k_tokens=payload.input_cost_per_1k_tokens,
        output_cost_per_1k_tokens=payload.output_cost_per_1k_tokens,
        supports_streaming=payload.supports_streaming,
        supports_function_calling=payload.supports_function_calling,
        supports_vision=payload.supports_vision,
        extra_params=payload.extra_params,
        is_active=True,
    )
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)

    logger.info("Registered LLM model", model_id=str(new_model.id), name=new_model.name)
    return new_model


@router.get(
    "/providers/{provider_id}/models",
    response_model=List[ModelResponse],
    summary="List all models for a provider",
)
async def list_models_for_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(LLMModel).where(LLMModel.provider_id == provider_id).order_by(LLMModel.name)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/models",
    response_model=List[ModelResponse],
    summary="List all registered models across all providers",
)
async def list_all_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(LLMModel).where(LLMModel.is_active == True).order_by(LLMModel.name)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch(
    "/models/{model_id}",
    response_model=ModelResponse,
    summary="Update model configuration or pricing",
)
async def update_model(
    model_id: uuid.UUID,
    payload: ModelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(LLMModel).where(LLMModel.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if payload.display_name is not None:
        model.display_name = payload.display_name
    if payload.aliases is not None:
        model.aliases = payload.aliases
    if payload.context_window is not None:
        model.context_window = payload.context_window
    if payload.max_output_tokens is not None:
        model.max_output_tokens = payload.max_output_tokens
    if payload.input_cost_per_1k_tokens is not None:
        model.input_cost_per_1k_tokens = payload.input_cost_per_1k_tokens
    if payload.output_cost_per_1k_tokens is not None:
        model.output_cost_per_1k_tokens = payload.output_cost_per_1k_tokens
    if payload.supports_streaming is not None:
        model.supports_streaming = payload.supports_streaming
    if payload.supports_function_calling is not None:
        model.supports_function_calling = payload.supports_function_calling
    if payload.supports_vision is not None:
        model.supports_vision = payload.supports_vision
    if payload.is_active is not None:
        model.is_active = payload.is_active
    if payload.extra_params is not None:
        model.extra_params = payload.extra_params

    await db.commit()
    await db.refresh(model)
    return model


@router.delete(
    "/models/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a registered model",
)
async def delete_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(LLMModel).where(LLMModel.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()
    return None

