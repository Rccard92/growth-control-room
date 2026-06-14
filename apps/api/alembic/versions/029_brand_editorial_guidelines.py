"""Revision ID: 029
Revises: 028
Create Date: 2026-06-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_editorial_guidelines",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("content_philosophy", sa.Text(), nullable=True),
        sa.Column("article_length_policy", sa.Text(), nullable=True),
        sa.Column("reading_style", sa.Text(), nullable=True),
        sa.Column("storytelling_rules", _jsonb, nullable=True),
        sa.Column("brand_people", _jsonb, nullable=True),
        sa.Column("author_voice_rules", _jsonb, nullable=True),
        sa.Column("community_cta_rules", _jsonb, nullable=True),
        sa.Column("article_dos", _jsonb, nullable=True),
        sa.Column("article_donts", _jsonb, nullable=True),
        sa.Column("default_article_length", sa.String(length=32), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_editorial_guidelines_project_id"),
    )
    op.create_index(
        "ix_brand_editorial_guidelines_project_id",
        "brand_editorial_guidelines",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_brand_editorial_guidelines_project_id",
        table_name="brand_editorial_guidelines",
    )
    op.drop_table("brand_editorial_guidelines")
