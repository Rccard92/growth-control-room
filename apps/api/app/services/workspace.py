from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import DEFAULT_WORKSPACE_NAME, Workspace


async def get_workspace_for_user(session: AsyncSession, user: User) -> Workspace:
    """The workspace the signed-in user owns.

    Every project query is scoped through here, so a user can never reach another
    tenant's data by guessing a project id.
    """
    result = await session.execute(
        select(Workspace)
        .where(Workspace.owner_user_id == user.id)
        .order_by(Workspace.created_at.asc())
    )
    workspace = result.scalars().first()
    if workspace is None:
        raise RuntimeError(
            f"Nessun workspace associato all'utente {user.email}. "
            "Esegui le migration e il bootstrap iniziale."
        )
    return workspace


async def get_default_workspace(session: AsyncSession) -> Workspace:
    """Legacy single-tenant lookup, kept for the initial bootstrap only."""
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
