"""Encryption at rest for integration secrets (OAuth tokens, API keys).

Payloads are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) and stored with a
version prefix so keys can be rotated and legacy rows can still be read.

Formats handled on read:
  ``v2:<fernet token>``  current
  ``plain:<base64>``     legacy, base64 only -- NOT encryption (see migration 044)
  anything else          treated as an unencrypted literal

Configure ``SECRETS_ENCRYPTION_KEY`` with one or more comma-separated Fernet keys.
The first key encrypts; the others are accepted on decrypt, which is what makes
rotation possible: add the new key in front, redeploy, re-encrypt, drop the old one.

Generate a key with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

import base64
import logging

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import settings

logger = logging.getLogger(__name__)

_V2_PREFIX = "v2:"
_LEGACY_PREFIX = "plain:"

# Used only when APP_ENV=development and no key is configured, so a local database
# stays readable across restarts. Never reachable in production: the settings
# validator refuses to boot without a real key.
_DEV_FALLBACK_KEY = base64.urlsafe_b64encode(b"gcr-development-only-key-32bytes").decode()

_cached_fernet: MultiFernet | None = None
_cached_keys: str | None = None


class SecretsKeyMissingError(RuntimeError):
    """No usable encryption key is configured."""


def _resolve_keys() -> list[str]:
    raw = (settings.secrets_encryption_key or "").strip()
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if keys:
        return keys
    if settings.app_env == "development":
        logger.warning(
            "SECRETS_ENCRYPTION_KEY not set: using the development fallback key. "
            "Never run production without a real key."
        )
        return [_DEV_FALLBACK_KEY]
    raise SecretsKeyMissingError(
        "SECRETS_ENCRYPTION_KEY is required to read or write integration secrets."
    )


def _fernet() -> MultiFernet:
    global _cached_fernet, _cached_keys
    keys = _resolve_keys()
    cache_key = ",".join(keys)
    if _cached_fernet is None or _cached_keys != cache_key:
        try:
            _cached_fernet = MultiFernet([Fernet(k.encode()) for k in keys])
        except (ValueError, TypeError) as exc:
            raise SecretsKeyMissingError(
                "SECRETS_ENCRYPTION_KEY is not a valid Fernet key. Generate one with: "
                'python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ) from exc
        _cached_keys = cache_key
    return _cached_fernet


def reset_encryption_cache() -> None:
    """Drop the cached key material (tests, key rotation)."""
    global _cached_fernet, _cached_keys
    _cached_fernet, _cached_keys = None, None


def encrypt_secret(value: str) -> str:
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{_V2_PREFIX}{token}"


def is_legacy_secret(value: str | None) -> bool:
    """True for values stored before real encryption was introduced."""
    return bool(value) and value.startswith(_LEGACY_PREFIX)


def decrypt_secret(value: str) -> str:
    if value.startswith(_V2_PREFIX):
        try:
            return _fernet().decrypt(value[len(_V2_PREFIX) :].encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretsKeyMissingError(
                "Unable to decrypt an integration secret: the current "
                "SECRETS_ENCRYPTION_KEY does not match the one used to encrypt it."
            ) from exc
    if value.startswith(_LEGACY_PREFIX):
        # Legacy base64 rows. Migration 044 re-encrypts them; this branch keeps a
        # database that has not been migrated yet readable.
        return base64.b64decode(value[len(_LEGACY_PREFIX) :].encode("ascii")).decode("utf-8")
    return value
