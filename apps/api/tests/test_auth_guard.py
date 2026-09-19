"""Every endpoint must require a session, except an explicit public allowlist.

This is the test that has to fail loudly if someone adds a route and forgets the
guard -- the whole API used to be reachable without any credentials at all.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Callable without a session, and why.
PUBLIC_PATHS = {
    "/health": "liveness probe",
    "/api/health": "liveness probe",
    "/api/auth/login": "sign-in itself",
    "/api/integrations/shopify/oauth/callback": "called by Shopify, authenticated by signed state",
    "/api/google/oauth/callback": "called by Google, authenticated by signed state",
}

# Authenticated at handler level rather than by the router guard.
HANDLER_GUARDED = {"/api/auth/me", "/api/auth/logout", "/api/auth/change-password"}

DUMMY_UUID = "00000000-0000-0000-0000-000000000000"


def _concrete_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", DUMMY_UUID, path)


def _all_operations() -> list[tuple[str, str]]:
    spec = app.openapi()
    return [
        (method.upper(), path)
        for path, operations in spec["paths"].items()
        for method in operations
        if method.lower() in ("get", "post", "put", "patch", "delete")
    ]


@pytest.fixture(scope="module")
def client():
    # No lifespan: the guard must answer before anything touches the database.
    return TestClient(app)


def test_every_route_rejects_anonymous_requests(client) -> None:
    unprotected: list[str] = []
    for method, path in _all_operations():
        if path in PUBLIC_PATHS:
            continue
        response = client.request(method, _concrete_path(path))
        if response.status_code != 401:
            unprotected.append(f"{method} {path} -> {response.status_code}")

    assert not unprotected, "Endpoint raggiungibili senza autenticazione:\n" + "\n".join(
        unprotected
    )


def test_handler_guarded_auth_routes_are_covered(client) -> None:
    for path in HANDLER_GUARDED:
        assert client.get(_concrete_path(path)).status_code in (401, 405)


def test_malformed_authorization_headers_are_rejected(client) -> None:
    """These never reach the database: a bad header is refused up front."""
    for header in (
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer    "},
        {"Authorization": ""},
    ):
        assert client.get("/api/auth/me", headers=header).status_code == 401


def test_unknown_bearer_token_is_rejected(client) -> None:
    """A well-formed token that matches no session must not authenticate."""
    from app.db.session import get_db

    class _NoRows:
        def scalar_one_or_none(self):
            return None

    class _FakeSession:
        async def execute(self, *_args, **_kwargs):
            return _NoRows()

    async def _fake_db():
        yield _FakeSession()

    app.dependency_overrides[get_db] = _fake_db
    try:
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer inesistente"}
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_public_allowlist_has_not_silently_grown() -> None:
    spec = app.openapi()
    auth_free = {p for p in spec["paths"] if p in PUBLIC_PATHS}
    assert auth_free == set(PUBLIC_PATHS), (
        "La allowlist pubblica non corrisponde alle route esposte: "
        f"{auth_free ^ set(PUBLIC_PATHS)}"
    )
