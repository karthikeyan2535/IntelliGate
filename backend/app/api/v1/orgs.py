"""
Organizations & membership CRUD API.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database.base import get_db
from app.database.models import Organization, OrganizationMember, OrgRole, User
from app.schemas.common import PaginatedResponse
from app.schemas.orgs import (
    InviteMemberRequest,
    OrgCreateRequest,
    OrgMemberResponse,
    OrgResponse,
    OrgUpdateRequest,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


async def _get_org_or_404(org_id: uuid.UUID, db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


async def _require_org_role(
    org_id: uuid.UUID,
    user: User,
    db: AsyncSession,
    *allowed_roles: OrgRole,
) -> OrganizationMember:
    if user.is_superuser:
        member = OrganizationMember(organization_id=org_id, user_id=user.id, role=OrgRole.OWNER)
        return member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None or member.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return member


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    body: OrgCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already in use")

    org = Organization(name=body.name, slug=body.slug, description=body.description)
    db.add(org)
    await db.flush()

    # Make creator the owner
    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrgRole.OWNER,
    )
    db.add(member)
    return org


@router.get("", response_model=PaginatedResponse[OrgResponse])
async def list_orgs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[OrgResponse]:
    if current_user.is_superuser:
        base_q = select(Organization)
    else:
        base_q = (
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == current_user.id)
        )

    total_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = total_result.scalar_one()

    orgs_result = await db.execute(
        base_q.offset((page - 1) * page_size).limit(page_size)
    )
    orgs = orgs_result.scalars().all()
    return PaginatedResponse(
        items=[OrgResponse.model_validate(o) for o in orgs],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    org = await _get_org_or_404(org_id, db)
    await _require_org_role(
        org_id, current_user, db,
        OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER, OrgRole.VIEWER,
    )
    return org


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: uuid.UUID,
    body: OrgUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    org = await _get_org_or_404(org_id, db)
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    org = await _get_org_or_404(org_id, db)
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER)
    await db.delete(org)


@router.post("/{org_id}/members", response_model=OrgMemberResponse, status_code=201)
async def invite_member(
    org_id: uuid.UUID,
    body: InviteMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationMember:
    await _get_org_or_404(org_id, db)
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)

    # Verify user exists
    target = await db.execute(select(User).where(User.id == body.user_id))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == body.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    member = OrganizationMember(
        organization_id=org_id,
        user_id=body.user_id,
        role=body.role,
        invited_by_id=current_user.id,
    )
    db.add(member)
    await db.flush()
    return member


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await _get_org_or_404(org_id, db)
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
