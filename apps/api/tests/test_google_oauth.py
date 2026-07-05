"""Tests for Google OAuth state helpers."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.google.google_oauth import (
    _b64url_encode,
    _sign_state_payload,
    create_google_oauth_state,
    verify_google_oauth_state,
)


def test_create_and_verify_google_oauth_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.google.google_oauth.settings.google_oauth_client_secret",
        "test-secret",
    )
    project_id = uuid4()
    state = create_google_oauth_state(project_id)
    verified = verify_google_oauth_state(state)
    assert verified is not None
    assert verified.project_id == project_id
    assert verified.provider is None
    assert verified.mode == "connect"


def test_create_google_oauth_state_includes_provider_and_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.google.google_oauth.settings.google_oauth_client_secret",
        "test-secret",
    )
    project_id = uuid4()
    state = create_google_oauth_state(
        project_id,
        provider="merchant_center",
        mode="add_scope",
    )
    verified = verify_google_oauth_state(state)
    assert verified is not None
    assert verified.project_id == project_id
    assert verified.provider == "merchant_center"
    assert verified.mode == "add_scope"


def test_verify_google_oauth_state_rejects_tampered_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.google.google_oauth.settings.google_oauth_client_secret",
        "test-secret",
    )
    project_id = uuid4()
    state = create_google_oauth_state(project_id)
    payload, _signature = state.rsplit(".", 1)
    tampered = f"{payload}.deadbeef"
    assert verify_google_oauth_state(tampered) is None


def test_verify_google_oauth_state_rejects_expired_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.google.google_oauth.settings.google_oauth_client_secret",
        "test-secret",
    )
    project_id = uuid4()
    payload = {
        "project_id": str(project_id),
        "nonce": "nonce",
        "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign_state_payload(payload_b64)
    state = f"{payload_b64}.{signature}"
    assert verify_google_oauth_state(state) is None
