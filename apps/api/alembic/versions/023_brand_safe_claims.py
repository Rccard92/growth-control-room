"""Revision ID: 023
Revises: 022
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_safe_claims",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("allowed_claims", _jsonb, nullable=True),
        sa.Column("forbidden_claims", _jsonb, nullable=True),
        sa.Column("caution_claims", _jsonb, nullable=True),
        sa.Column("disclaimers", _jsonb, nullable=True),
        sa.Column("health_claim_rules", _jsonb, nullable=True),
        sa.Column("competitor_rules", _jsonb, nullable=True),
        sa.Column("process_secrets", _jsonb, nullable=True),
        sa.Column("tone_red_flags", _jsonb, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_import_source", sa.String(length=500), nullable=True),
        sa.Column("last_confidence", sa.Float(), nullable=True),
        sa.Column("warnings", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_safe_claims_project_id"),
    )
    op.create_index("ix_brand_safe_claims_project_id", "brand_safe_claims", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_brand_safe_claims_project_id", table_name="brand_safe_claims")
    op.drop_table("brand_safe_claims")
