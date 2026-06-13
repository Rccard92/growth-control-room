"""Revision ID: 018
Revises: 017
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_section_drafts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("batch_id", sa.UUID(), nullable=True),
        sa.Column("section_key", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("draft_payload", _jsonb, nullable=False, server_default="{}"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source_fact_ids", _jsonb, nullable=True),
        sa.Column("source_document_ids", _jsonb, nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column("warnings", _jsonb, nullable=True),
        sa.Column("previous_official_snapshot", _jsonb, nullable=True),
        sa.Column("approved_at", _ts, nullable=True),
        sa.Column("applied_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_id"], ["brand_import_batches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_section_drafts_project_id", "brand_section_drafts", ["project_id"])
    op.create_index("ix_brand_section_drafts_batch_id", "brand_section_drafts", ["batch_id"])
    op.create_index("ix_brand_section_drafts_section_key", "brand_section_drafts", ["section_key"])
    op.create_index("ix_brand_section_drafts_status", "brand_section_drafts", ["status"])
    op.create_index(
        "ix_brand_section_drafts_project_section_status",
        "brand_section_drafts",
        ["project_id", "section_key", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_brand_section_drafts_project_section_status", table_name="brand_section_drafts")
    op.drop_index("ix_brand_section_drafts_status", table_name="brand_section_drafts")
    op.drop_index("ix_brand_section_drafts_section_key", table_name="brand_section_drafts")
    op.drop_index("ix_brand_section_drafts_batch_id", table_name="brand_section_drafts")
    op.drop_index("ix_brand_section_drafts_project_id", table_name="brand_section_drafts")
    op.drop_table("brand_section_drafts")
