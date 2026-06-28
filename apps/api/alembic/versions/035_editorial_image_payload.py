"""Revision ID: 035
Revises: 034
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035"
down_revision: Union[str, None] = "034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("image_payload", _jsonb, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_seo_editorial_items", "image_payload")
