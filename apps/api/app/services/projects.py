from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.services.workspace import get_default_workspace


async def get_project_in_default_workspace(
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
