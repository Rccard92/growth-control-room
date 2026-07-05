import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.integrations import INTEGRATION_PROVIDERS
from app.db.session import get_db
from app.models.enums import IntegrationStatus
from app.models.integration import Integration
from app.models.project import Project
from app.schemas.integration import IntegrationRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.projects import get_project_in_default_workspace
from app.services.workspace import get_default_workspace
from app.utils.slug import unique_project_slug

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=ProjectRead,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_db),
) -> Project:
    try:
        workspace = await get_default_workspace(session)
        slug = await unique_project_slug(session, workspace.id, body.name)
        project = Project(
            workspace_id=workspace.id,
            name=body.name,
            slug=slug,
            description=body.description,
            public_site_url=body.public_site_url,
            status="active",
        )
        session.add(project)
        await session.flush()
        await session.refresh(project)
        return project
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Errore creazione progetto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "create_project_failed",
                "message": "Impossibile creare il progetto. Riprova più tardi.",
            },
        ) from exc


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
    return await get_project_in_default_workspace(project_id, session)


@router.patch("/{project_id}", response_model=ProjectRead, response_model_by_alias=True)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
) -> Project:
    try:
        project = await get_project_in_default_workspace(project_id, session)
        updates = body.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(project, field, value)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Errore aggiornamento progetto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_project_failed",
                "message": "Impossibile aggiornare il progetto. Riprova più tardi.",
            },
        ) from exc


@router.get(
    "/{project_id}/integrations",
    response_model=list[IntegrationRead],
    response_model_by_alias=True,
)
async def list_project_integrations(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[IntegrationRead]:
    project = await get_project_in_default_workspace(project_id, session)
    result = await session.execute(
        select(Integration).where(Integration.project_id == project.id)
    )
    stored = {integration.provider: integration for integration in result.scalars().all()}

    integrations: list[IntegrationRead] = []
    for provider in INTEGRATION_PROVIDERS:
        integration = stored.get(provider)
        if integration is None:
            integrations.append(
                IntegrationRead(
                    id=None,
                    project_id=project.id,
                    provider=provider,
                    status=IntegrationStatus.NOT_CONNECTED.value,
                    connected_at=None,
                )
            )
        else:
            integrations.append(
                IntegrationRead(
                    id=integration.id,
                    project_id=integration.project_id,
                    provider=integration.provider,
                    status=integration.status,
                    connected_at=integration.connected_at,
                )
            )
    return integrations
