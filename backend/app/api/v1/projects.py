"""
Projects CRUD API (scoped to an organization).
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.api.v1.orgs import _get_org_or_404, _require_org_role
from app.database.base import get_db
from app.database.models import OrgRole, Project, User
from app.schemas.common import PaginatedResponse
from app.schemas.orgs import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["Projects"])


async def _get_project_or_404(project_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.organization_id == org_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    org_id: uuid.UUID,
    body: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    await _get_org_or_404(org_id, db)
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)

    existing = await db.execute(
        select(Project).where(Project.organization_id == org_id, Project.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Project slug already in use in this org")

    project = Project(
        organization_id=org_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    org_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ProjectResponse]:
    await _get_org_or_404(org_id, db)
    await _require_org_role(
        org_id, current_user, db,
        OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER, OrgRole.VIEWER,
    )

    base_q = select(Project).where(Project.organization_id == org_id)
    total_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(base_q.offset((page - 1) * page_size).limit(page_size))
    projects = result.scalars().all()
    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    await _require_org_role(
        org_id, current_user, db,
        OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER, OrgRole.VIEWER,
    )
    return await _get_project_or_404(project_id, org_id, db)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)
    project = await _get_project_or_404(project_id, org_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await _require_org_role(org_id, current_user, db, OrgRole.OWNER, OrgRole.ADMIN)
    project = await _get_project_or_404(project_id, org_id, db)
    await db.delete(project)
