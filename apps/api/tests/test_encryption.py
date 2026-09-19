"""Integration secrets must be encrypted at rest, with rotation support."""

import base64

import pytest
from cryptography.fernet import Fernet

from app.core.config import settings
from app.services import encryption
from app.services.encryption import (
    SecretsKeyMissingError,
    decrypt_secret,
    encrypt_secret,
    is_legacy_secret,
    reset_encryption_cache,
)

TOKEN = "shpat_esempio_di_token_scrivibile"


@pytest.fixture
def key_setting(monkeypatch):
    def _set(value):
        monkeypatch.setattr(settings, "secrets_encryption_key", value)
        reset_encryption_cache()

    yield _set
    reset_encryption_cache()


def test_roundtrip(key_setting) -> None:
    key_setting(Fernet.generate_key().decode())
    stored = encrypt_secret(TOKEN)
    assert stored.startswith("v2:")
    assert TOKEN not in stored
    assert base64.b64encode(TOKEN.encode()).decode() not in stored
    assert decrypt_secret(stored) == TOKEN


def test_ciphertext_is_not_deterministic(key_setting) -> None:
    key_setting(Fernet.generate_key().decode())
    assert encrypt_secret(TOKEN) != encrypt_secret(TOKEN)


def test_legacy_base64_payloads_are_still_readable(key_setting) -> None:
    key_setting(Fernet.generate_key().decode())
    legacy = "plain:" + base64.b64encode(TOKEN.encode()).decode()
    assert is_legacy_secret(legacy)
    assert decrypt_secret(legacy) == TOKEN


def test_key_rotation_reads_old_and_writes_new(key_setting) -> None:
    old_key = Fernet.generate_key().decode()
    key_setting(old_key)
    old_payload = encrypt_secret(TOKEN)

    new_key = Fernet.generate_key().decode()
    key_setting(f"{new_key},{old_key}")

    assert decrypt_secret(old_payload) == TOKEN
    new_payload = encrypt_secret(TOKEN)

    key_setting(new_key)
    assert decrypt_secret(new_payload) == TOKEN


def test_wrong_key_raises_instead_of_returning_garbage(key_setting) -> None:
    key_setting(Fernet.generate_key().decode())
    payload = encrypt_secret(TOKEN)
    key_setting(Fernet.generate_key().decode())
    with pytest.raises(SecretsKeyMissingError):
        decrypt_secret(payload)


def test_production_without_key_refuses(key_setting, monkeypatch) -> None:
    key_setting(None)
    monkeypatch.setattr(settings, "app_env", "production")
    encryption.reset_encryption_cache()
    with pytest.raises(SecretsKeyMissingError):
        encrypt_secret(TOKEN)


def test_invalid_key_reports_how_to_generate_one(key_setting) -> None:
    key_setting("not-a-fernet-key")
    with pytest.raises(SecretsKeyMissingError, match="Fernet"):
        encrypt_secret(TOKEN)
