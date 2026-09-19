"""Shared fixtures for tests that call route handlers directly."""

from types import SimpleNamespace
from uuid import UUID

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")

#: Stand-in for the authenticated user. Handlers only pass it through to
#: `get_project_for_user`, which these tests patch, so a namespace is enough.
TEST_USER = SimpleNamespace(
    id=TEST_USER_ID,
    email="test@gcr.local",
    name="Test",
    is_active=True,
    password_hash=None,
    last_login_at=None,
)
