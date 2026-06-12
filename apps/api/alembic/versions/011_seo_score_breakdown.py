"""seo score breakdown column

Revision ID: 011
Revises: 010
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "seo_entity_analyses",
        sa.Column("score_breakdown", _jsonb, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("seo_entity_analyses", "score_breakdown")
