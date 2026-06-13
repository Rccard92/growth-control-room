"""Revision ID: 012
Revises: 011
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column("shopify_stores", sa.Column("granted_scopes", _jsonb, nullable=True))
    op.add_column(
        "shopify_stores",
        sa.Column("scopes_checked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shopify_stores", "scopes_checked_at")
    op.drop_column("shopify_stores", "granted_scopes")
