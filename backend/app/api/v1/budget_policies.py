"""
Budget policies management API.
Enforces spending caps and alerts per organization or project.
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
from app.database.models import BudgetPolicy, Organization, User
from app.schemas.budget import (
    BudgetPolicyCreateRequest,
    BudgetPolicyResponse,
    BudgetPolicyUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Budget Policies"])


@router.post(
    "/orgs/{org_id}/budgets",
    response_model=BudgetPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget policy for an organization",
)
async def create_budget_policy(
    org_id: uuid.UUID,
    payload: BudgetPolicyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Organization).where(Organization.id == org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    new_policy = BudgetPolicy(
        organization_id=org_id,
        name=payload.name,
        period=payload.period,
        limit_usd=payload.limit_usd,
        alert_threshold_pct=payload.alert_threshold_pct,
        hard_limit=payload.hard_limit,
        is_active=True,
    )
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)

    logger.info("Created budget policy", policy_id=str(new_policy.id), org_id=str(org_id))
    return new_policy


@router.get(
    "/orgs/{org_id}/budgets",
    response_model=List[BudgetPolicyResponse],
    summary="List budget policies for an organization",
)
async def list_budget_policies(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(BudgetPolicy).where(BudgetPolicy.organization_id == org_id).order_by(BudgetPolicy.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch(
    "/budgets/{policy_id}",
    response_model=BudgetPolicyResponse,
    summary="Update budget policy limit or settings",
)
async def update_budget_policy(
    policy_id: uuid.UUID,
    payload: BudgetPolicyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(BudgetPolicy).where(BudgetPolicy.id == policy_id)
    res = await db.execute(stmt)
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Budget policy not found")

    if payload.name is not None:
        policy.name = payload.name
    if payload.period is not None:
        policy.period = payload.period
    if payload.limit_usd is not None:
        policy.limit_usd = payload.limit_usd
    if payload.alert_threshold_pct is not None:
        policy.alert_threshold_pct = payload.alert_threshold_pct
    if payload.hard_limit is not None:
        policy.hard_limit = payload.hard_limit
    if payload.is_active is not None:
        policy.is_active = payload.is_active

    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete(
    "/budgets/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget policy",
)
async def delete_budget_policy(
    policy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(BudgetPolicy).where(BudgetPolicy.id == policy_id)
    res = await db.execute(stmt)
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Budget policy not found")

    await db.delete(policy)
    await db.commit()
    return None

