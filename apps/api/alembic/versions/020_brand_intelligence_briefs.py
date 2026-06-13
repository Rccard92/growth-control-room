"""Revision ID: 020
Revises: 019
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_intelligence_briefs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("source_batch_id", sa.UUID(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "brief_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("markdown_summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_document_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_external_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_fact_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approved_at", _ts, nullable=True),
        sa.Column("archived_at", _ts, nullable=True),
        sa.Column("created_at", _ts, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", _ts, nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_batch_id"], ["brand_import_batches.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_brand_intelligence_briefs_project_id",
        "brand_intelligence_briefs",
        ["project_id"],
    )
    op.create_index(
        "ix_brand_intelligence_briefs_source_batch_id",
        "brand_intelligence_briefs",
        ["source_batch_id"],
    )
    op.create_index(
        "ix_brand_intelligence_briefs_status",
        "brand_intelligence_briefs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_brand_intelligence_briefs_status", table_name="brand_intelligence_briefs")
    op.drop_index(
        "ix_brand_intelligence_briefs_source_batch_id",
        table_name="brand_intelligence_briefs",
    )
    op.drop_index(
        "ix_brand_intelligence_briefs_project_id",
        table_name="brand_intelligence_briefs",
    )
    op.drop_table("brand_intelligence_briefs")
