"""Create the first administrator account on startup.

Driven by INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD. It only ever creates the
account when none has a password yet, so restarts never reset an existing one.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.workspace import DEFAULT_WORKSPACE_NAME, Workspace
from app.services.auth.passwords import (
    WeakPasswordError,
    hash_password,
    validate_password_strength,
)

logger = logging.getLogger(__name__)


async def ensure_initial_admin(session: AsyncSession) -> bool:
    """Return True when an admin account was created by this call."""
    email = (settings.initial_admin_email or "").strip().lower()
    password = settings.initial_admin_password or ""
    if not email or not password:
        return False

    existing_with_password = (
        await session.execute(
            select(func.count()).select_from(User).where(User.password_hash.is_not(None))
        )
    ).scalar_one()
    if existing_with_password:
        return False

    try:
        validate_password_strength(password)
    except WeakPasswordError as exc:
        logger.error("INITIAL_ADMIN_PASSWORD rifiutata: %s", exc)
        return False

    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(email=email, name=email.split("@")[0], is_active=True)
        session.add(user)
        await session.flush()

    user.password_hash = hash_password(password)
    user.is_active = True

    # Attach the account to a workspace so project queries have somewhere to land.
    owned = (
        (await session.execute(select(Workspace).where(Workspace.owner_user_id == user.id)))
        .scalars()
        .first()
    )
    if owned is None:
        orphan = (
            await session.execute(select(Workspace).where(Workspace.name == DEFAULT_WORKSPACE_NAME))
        ).scalar_one_or_none()
        if orphan is not None:
            orphan.owner_user_id = user.id
        else:
            session.add(Workspace(name=DEFAULT_WORKSPACE_NAME, owner_user_id=user.id))

    await session.commit()
    logger.info("Account amministratore iniziale creato per %s", email)
    return True
