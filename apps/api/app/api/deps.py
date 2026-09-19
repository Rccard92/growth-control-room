"""Shared FastAPI dependencies: authentication and tenant scoping."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth.sessions import resolve_session_user

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Autenticazione richiesta.",
    headers={"WWW-Authenticate": "Bearer"},
)


def bearer_token(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


async def get_current_user(
    token: str | None = Depends(bearer_token),
    session: AsyncSession = Depends(get_db),
) -> User:
    if token is None:
        raise _UNAUTHENTICATED
    user = await resolve_session_user(session, token)
    if user is None:
        raise _UNAUTHENTICATED
    return user


async def require_user(user: User = Depends(get_current_user)) -> User:
    """Router-level guard. Use as `dependencies=[Depends(require_user)]`."""
    return user
