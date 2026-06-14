"""Revision ID: 025
Revises: 024
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_faq_objections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("general_faq", _jsonb, nullable=True),
        sa.Column("product_process_questions", _jsonb, nullable=True),
        sa.Column("purchase_shipping_questions", _jsonb, nullable=True),
        sa.Column("objections", _jsonb, nullable=True),
        sa.Column("myths_misconceptions", _jsonb, nullable=True),
        sa.Column("recommended_answers", _jsonb, nullable=True),
        sa.Column("content_opportunities", _jsonb, nullable=True),
        sa.Column("social_comment_insights", _jsonb, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_import_source", sa.String(length=500), nullable=True),
        sa.Column("last_confidence", sa.Float(), nullable=True),
        sa.Column("warnings", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_faq_objections_project_id"),
    )
    op.create_index("ix_brand_faq_objections_project_id", "brand_faq_objections", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_brand_faq_objections_project_id", table_name="brand_faq_objections")
    op.drop_table("brand_faq_objections")
