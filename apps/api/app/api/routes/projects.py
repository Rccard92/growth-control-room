from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.integration import Integration
from app.models.project import Project
from app.schemas.integration import IntegrationRead
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.workspace import get_default_workspace

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_in_default_workspace(
    project_id: UUID,
    session: AsyncSession,
) -> Project:
    workspace = await get_default_workspace(session)
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.workspace_id == workspace.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progetto non trovato",
        )
    return project


@router.post(
    "",
    response_model=ProjectRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_db),
) -> Project:
    workspace = await get_default_workspace(session)
    project = Project(
        workspace_id=workspace.id,
        name=body.name,
        brand=body.brand,
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead], response_model_by_alias=True)
async def list_projects(
    session: AsyncSession = Depends(get_db),
) -> list[Project]:
    workspace = await get_default_workspace(session)
    result = await session.execute(
        select(Project)
        .where(Project.workspace_id == workspace.id)
        .order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectRead, response_model_by_alias=True)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> Project:
    return await _get_project_in_default_workspace(project_id, session)


@router.get(
    "/{project_id}/integrations",
    response_model=list[IntegrationRead],
    response_model_by_alias=True,
)
async def list_project_integrations(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[Integration]:
    await _get_project_in_default_workspace(project_id, session)
    result = await session.execute(
        select(Integration)
        .where(Integration.project_id == project_id)
        .order_by(Integration.type)
    )
    return list(result.scalars().all())
