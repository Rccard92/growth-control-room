from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import DEFAULT_WORKSPACE_SLUG, Workspace


async def get_default_workspace(session: AsyncSession) -> Workspace:
    result = await session.execute(
        select(Workspace).where(Workspace.slug == DEFAULT_WORKSPACE_SLUG)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise RuntimeError(
            f"Workspace default '{DEFAULT_WORKSPACE_SLUG}' non trovato. "
            "Esegui le migration: pnpm db:migrate"
        )
    return workspace
