"""Re-encrypt legacy base64 integration credentials with Fernet.

Rows written before real encryption existed are stored as ``plain:<base64>``,
which is encoding, not encryption. This migration rewrites them as ``v2:<fernet>``.

Requires SECRETS_ENCRYPTION_KEY to be set (in development a fallback key is used).

Revision ID: 044
Revises: 043
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "044"
down_revision: Union[str, None] = "043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CREDENTIALS = sa.table(
    "integration_credentials",
    sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
    sa.column("encrypted_payload", sa.Text),
)


def upgrade() -> None:
    from app.services.encryption import decrypt_secret, encrypt_secret

    connection = op.get_bind()
    rows = connection.execute(
        sa.select(_CREDENTIALS.c.id, _CREDENTIALS.c.encrypted_payload).where(
            _CREDENTIALS.c.encrypted_payload.like("plain:%")
        )
    ).fetchall()

    for row_id, payload in rows:
        connection.execute(
            _CREDENTIALS.update()
            .where(_CREDENTIALS.c.id == row_id)
            .values(encrypted_payload=encrypt_secret(decrypt_secret(payload)))
        )


def downgrade() -> None:
    """Rewrite Fernet payloads back to the legacy base64 format."""
    import base64

    from app.services.encryption import decrypt_secret

    connection = op.get_bind()
    rows = connection.execute(
        sa.select(_CREDENTIALS.c.id, _CREDENTIALS.c.encrypted_payload).where(
            _CREDENTIALS.c.encrypted_payload.like("v2:%")
        )
    ).fetchall()

    for row_id, payload in rows:
        legacy = base64.b64encode(decrypt_secret(payload).encode("utf-8")).decode("ascii")
        connection.execute(
            _CREDENTIALS.update()
            .where(_CREDENTIALS.c.id == row_id)
            .values(encrypted_payload=f"plain:{legacy}")
        )
