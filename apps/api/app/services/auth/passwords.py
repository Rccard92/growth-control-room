"""Password hashing with scrypt from the standard library.

Format: ``scrypt$<n>$<r>$<p>$<salt b64>$<hash b64>``. Parameters are stored with
the hash so they can be raised later without invalidating existing passwords.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_N = 2**15
_R = 8
_P = 1
_DKLEN = 64
_SALT_BYTES = 16
_PREFIX = "scrypt"

MIN_PASSWORD_LENGTH = 12


class WeakPasswordError(ValueError):
    """The password does not meet the minimum policy."""


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"La password deve avere almeno {MIN_PASSWORD_LENGTH} caratteri."
        )
    if password.strip() != password:
        raise WeakPasswordError("La password non può iniziare o finire con spazi.")
    if password.lower() in {"password1234", "growthcontrolroom", "changeme1234"}:
        raise WeakPasswordError("Password troppo comune, scegline un'altra.")


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN
    )
    return f"{_PREFIX}${_N}${_R}${_P}${_b64(salt)}${_b64(derived)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        prefix, n_raw, r_raw, p_raw, salt_b64, hash_b64 = stored.split("$")
        if prefix != _PREFIX:
            return False
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=base64.b64decode(salt_b64),
            n=int(n_raw),
            r=int(r_raw),
            p=int(p_raw),
            dklen=len(base64.b64decode(hash_b64)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, base64.b64decode(hash_b64))
