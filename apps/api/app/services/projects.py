from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.services.workspace import get_workspace_for_user


async def get_project_for_user(
    project_id: UUID,
    session: AsyncSession,
    user: User,
) -> Project:
    """Load a project, or 404 if it does not belong to the user's workspace.

    404 rather than 403 on purpose: a wrong tenant should not learn that the id exists.
    """
    workspace = await get_workspace_for_user(session, user)
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


async def get_project_by_id(project_id: UUID, session: AsyncSession) -> Project:
    """Load a project without a tenant check.

    Only for code reached from a route that already called `get_project_for_user`.
    Never call it straight from a route handler.
    """
    project = (
        await session.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progetto non trovato",
        )
    return project
