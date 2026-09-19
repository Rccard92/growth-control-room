"""Opaque bearer sessions stored server-side.

A random token is handed to the client; only its SHA-256 digest is stored, so a
database dump does not yield usable sessions. Server-side storage also means
logout and "revoke everything" actually work, which a stateless JWT cannot do.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user_session import UserSession

SESSION_TTL = timedelta(days=14)
# Sliding window: an active session is extended, an idle one expires.
SESSION_REFRESH_AFTER = timedelta(hours=12)
_TOKEN_BYTES = 32


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


async def create_session(
    session: AsyncSession,
    user: User,
    *,
    user_agent: str | None = None,
) -> tuple[str, UserSession]:
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    row = UserSession(
        user_id=user.id,
        token_hash=_digest(token),
        expires_at=_now() + SESSION_TTL,
        last_used_at=_now(),
        user_agent=(user_agent or "")[:255] or None,
    )
    session.add(row)
    await session.flush()
    return token, row


async def resolve_session_user(session: AsyncSession, token: str) -> User | None:
    if not token:
        return None
    result = await session.execute(
        select(UserSession)
        .where(UserSession.token_hash == _digest(token))
        .options(selectinload(UserSession.user))
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= _now():
        await session.delete(row)
        return None

    user = row.user
    if user is None or not user.is_active:
        return None

    last_used = row.last_used_at
    if last_used is not None and last_used.tzinfo is None:
        last_used = last_used.replace(tzinfo=UTC)
    if last_used is None or _now() - last_used > SESSION_REFRESH_AFTER:
        row.last_used_at = _now()
        row.expires_at = _now() + SESSION_TTL
    return user


async def revoke_session(session: AsyncSession, token: str) -> None:
    await session.execute(delete(UserSession).where(UserSession.token_hash == _digest(token)))


async def revoke_all_sessions_for_user(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(delete(UserSession).where(UserSession.user_id == user_id))


async def purge_expired_sessions(session: AsyncSession) -> int:
    result = await session.execute(delete(UserSession).where(UserSession.expires_at <= _now()))
    return result.rowcount or 0


async def touch_last_login(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(update(User).where(User.id == user_id).values(last_login_at=_now()))
