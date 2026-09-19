"""Sign-in, sign-out and password management."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import bearer_token, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, UserRead
from app.services.auth.passwords import (
    WeakPasswordError,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.services.auth.sessions import (
    create_session,
    revoke_all_sessions_for_user,
    revoke_session,
    touch_last_login,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email o password non corretti.",
)


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=str(user.id),
        email=user.email,
        name=user.name,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = (
        await session.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()

    # Always run the hash comparison so a missing account and a wrong password
    # take the same time and cannot be told apart by timing.
    password_ok = verify_password(body.password, user.password_hash if user else None)
    if user is None or not password_ok or not user.is_active:
        logger.info("Login fallito per %s", body.email)
        raise _INVALID_CREDENTIALS

    token, row = await create_session(
        session, user, user_agent=request.headers.get("user-agent")
    )
    await touch_last_login(session, user.id)
    await session.commit()
    await session.refresh(user)

    return LoginResponse(
        access_token=token,
        expires_at=row.expires_at,
        user=_user_read(user),
    )


@router.get("/me", response_model=UserRead, response_model_by_alias=True)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return _user_read(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str | None = Depends(bearer_token),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    if token:
        await revoke_session(session, token)
        await session.commit()


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    authorization: str | None = Header(default=None),
) -> None:
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password attuale non è corretta.",
        )
    try:
        validate_password_strength(body.new_password)
    except WeakPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    current_user.password_hash = hash_password(body.new_password)
    # Changing the password signs out every device, including this one.
    await revoke_all_sessions_for_user(session, current_user.id)
    await session.commit()
