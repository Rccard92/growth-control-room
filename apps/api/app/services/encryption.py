"""Placeholder encryption for integration secrets.

Replace with Fernet/KMS in production. Never log decrypted values.
"""

import base64

_PLAIN_PREFIX = "plain:"


def encrypt_secret(value: str) -> str:
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    return f"{_PLAIN_PREFIX}{encoded}"


def decrypt_secret(value: str) -> str:
    if value.startswith(_PLAIN_PREFIX):
        encoded = value[len(_PLAIN_PREFIX) :]
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    return value
