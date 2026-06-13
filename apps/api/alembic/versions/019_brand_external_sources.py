"""Revision ID: 019
Revises: 018
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column(
        "brand_import_batches",
        sa.Column("declared_brand_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "brand_import_batches",
        sa.Column("declared_website_url", sa.String(length=2000), nullable=True),
    )

    op.add_column(
        "brand_section_drafts",
        sa.Column(
            "source_external_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.create_table(
        "brand_external_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("batch_id", sa.UUID(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("fetched_title", sa.Text(), nullable=True),
        sa.Column("fetched_text", sa.Text(), nullable=True),
        sa.Column("fetched_summary", sa.Text(), nullable=True),
        sa.Column("fetch_error", sa.Text(), nullable=True),
        sa.Column("last_fetched_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_id"], ["brand_import_batches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_external_sources_project_id", "brand_external_sources", ["project_id"])
    op.create_index("ix_brand_external_sources_batch_id", "brand_external_sources", ["batch_id"])
    op.create_index(
        "ix_brand_external_sources_batch_type",
        "brand_external_sources",
        ["batch_id", "source_type"],
    )

    op.add_column(
        "brand_extracted_facts",
        sa.Column("source_external_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_brand_extracted_facts_source_external_id",
        "brand_extracted_facts",
        "brand_external_sources",
        ["source_external_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_brand_extracted_facts_source_external_id",
        "brand_extracted_facts",
        ["source_external_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_brand_extracted_facts_source_external_id", table_name="brand_extracted_facts")
    op.drop_constraint(
        "fk_brand_extracted_facts_source_external_id",
        "brand_extracted_facts",
        type_="foreignkey",
    )
    op.drop_column("brand_extracted_facts", "source_external_id")

    op.drop_index("ix_brand_external_sources_batch_type", table_name="brand_external_sources")
    op.drop_index("ix_brand_external_sources_batch_id", table_name="brand_external_sources")
    op.drop_index("ix_brand_external_sources_project_id", table_name="brand_external_sources")
    op.drop_table("brand_external_sources")

    op.drop_column("brand_section_drafts", "source_external_ids")
    op.drop_column("brand_import_batches", "declared_website_url")
    op.drop_column("brand_import_batches", "declared_brand_name")
