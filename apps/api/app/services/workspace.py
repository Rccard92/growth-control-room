from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import DEFAULT_WORKSPACE_NAME, Workspace


async def get_default_workspace(session: AsyncSession) -> Workspace:
    result = await session.execute(
        select(Workspace).where(Workspace.name == DEFAULT_WORKSPACE_NAME)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise RuntimeError(
            f"Workspace demo '{DEFAULT_WORKSPACE_NAME}' non trovato. "
            "Esegui le migration: alembic upgrade head"
        )
    return workspace
