"""Password hashing, bearer sessions and the login handler."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.auth import login
from app.schemas.auth import LoginRequest
from app.services.auth.passwords import (
    WeakPasswordError,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.services.auth.sessions import SESSION_TTL, resolve_session_user

PASSWORD = "una-password-robusta-2026"


# -- passwords ------------------------------------------------------------


def test_hash_is_salted_and_verifies() -> None:
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second, "ogni hash deve avere un salt diverso"
    assert PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert verify_password(PASSWORD, second)


def test_wrong_password_and_missing_hash_are_rejected() -> None:
    stored = hash_password(PASSWORD)
    assert not verify_password("sbagliata", stored)
    assert not verify_password(PASSWORD, None)
    assert not verify_password(PASSWORD, "")
    assert not verify_password(PASSWORD, "formato-non-valido")


def test_password_policy() -> None:
    validate_password_strength(PASSWORD)
    for weak in ("corta", " " + PASSWORD, "password1234"):
        with pytest.raises(WeakPasswordError):
            validate_password_strength(weak)


# -- sessions -------------------------------------------------------------


def _session_row(*, expires_in: timedelta, active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        expires_at=datetime.now(UTC) + expires_in,
        last_used_at=datetime.now(UTC) - timedelta(days=1),
        user=SimpleNamespace(id=uuid4(), email="a@b.it", is_active=active),
    )


def _fake_session(row):
    fake = AsyncMock()
    fake.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: row))
    fake.delete = AsyncMock()
    return fake


def test_valid_session_resolves_the_user_and_slides_the_expiry() -> None:
    row = _session_row(expires_in=timedelta(days=3))
    session = _fake_session(row)

    user = asyncio.run(resolve_session_user(session, "token"))

    assert user is row.user
    assert row.expires_at > datetime.now(UTC) + SESSION_TTL - timedelta(minutes=1)


def test_expired_session_is_rejected_and_deleted() -> None:
    row = _session_row(expires_in=-timedelta(seconds=1))
    session = _fake_session(row)

    assert asyncio.run(resolve_session_user(session, "token")) is None
    session.delete.assert_awaited_once_with(row)


def test_session_of_a_deactivated_user_is_rejected() -> None:
    row = _session_row(expires_in=timedelta(days=3), active=False)
    assert asyncio.run(resolve_session_user(_fake_session(row), "token")) is None


def test_unknown_and_empty_tokens_are_rejected() -> None:
    assert asyncio.run(resolve_session_user(_fake_session(None), "token")) is None
    assert asyncio.run(resolve_session_user(_fake_session(None), "")) is None


# -- login ----------------------------------------------------------------


def _request() -> SimpleNamespace:
    return SimpleNamespace(headers={"user-agent": "pytest"})


def _login_session(user):
    session = AsyncMock()
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: user))
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


def _active_user():
    return SimpleNamespace(
        id=uuid4(),
        email="admin@gcr.local",
        name="Admin",
        password_hash=hash_password(PASSWORD),
        is_active=True,
        last_login_at=None,
    )


def test_login_returns_a_token_for_valid_credentials() -> None:
    user = _active_user()
    session = _login_session(user)
    expires = datetime.now(UTC) + SESSION_TTL

    with patch(
        "app.api.routes.auth.create_session",
        new=AsyncMock(return_value=("tok-abc", SimpleNamespace(expires_at=expires))),
    ):
        response = asyncio.run(
            login(
                LoginRequest(email="Admin@GCR.local", password=PASSWORD),
                _request(),
                session,
            )
        )

    assert response.access_token == "tok-abc"
    assert response.user.email == "admin@gcr.local"


def test_login_rejects_a_wrong_password() -> None:
    session = _login_session(_active_user())
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            login(LoginRequest(email="admin@gcr.local", password="sbagliata"), _request(), session)
        )
    assert exc_info.value.status_code == 401


def test_login_rejects_an_unknown_account_with_the_same_error() -> None:
    session = _login_session(None)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            login(LoginRequest(email="ignoto@gcr.local", password=PASSWORD), _request(), session)
        )
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Email o password non corretti."


def test_login_rejects_a_deactivated_account() -> None:
    user = _active_user()
    user.is_active = False
    session = _login_session(user)
    with pytest.raises(HTTPException):
        asyncio.run(
            login(LoginRequest(email="admin@gcr.local", password=PASSWORD), _request(), session)
        )


def test_email_is_normalized_before_lookup() -> None:
    assert LoginRequest(email="  Admin@GCR.Local ", password="x").email == "admin@gcr.local"
    with pytest.raises(ValueError):
        LoginRequest(email="non-una-email", password="x")
