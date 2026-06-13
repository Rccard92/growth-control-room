"""Revision ID: 017
Revises: 016
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_import_batches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="file_upload"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(length=500), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_facts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_facts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_facts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("needs_review_facts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("warnings", _jsonb, nullable=True),
        sa.Column("started_at", _ts, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_import_batches_project_id", "brand_import_batches", ["project_id"])

    op.add_column("brand_source_documents", sa.Column("batch_id", sa.UUID(), nullable=True))
    op.add_column("brand_source_documents", sa.Column("processing_order", sa.Integer(), nullable=True))
    op.add_column(
        "brand_source_documents",
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("brand_source_documents", sa.Column("current_step", sa.String(length=500), nullable=True))
    op.add_column(
        "brand_source_documents",
        sa.Column("extracted_facts_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "brand_source_documents",
        sa.Column("needs_review_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "brand_source_documents",
        sa.Column("approved_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "brand_source_documents",
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_brand_source_documents_batch_id",
        "brand_source_documents",
        "brand_import_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_brand_source_documents_batch_id", "brand_source_documents", ["batch_id"])

    op.add_column("brand_extracted_facts", sa.Column("batch_id", sa.UUID(), nullable=True))
    op.add_column(
        "brand_extracted_facts",
        sa.Column("is_update_suggestion", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("brand_extracted_facts", sa.Column("existing_target_id", sa.UUID(), nullable=True))
    op.add_column(
        "brand_extracted_facts",
        sa.Column("update_mode", sa.String(length=50), nullable=False, server_default="create"),
    )
    op.add_column("brand_extracted_facts", sa.Column("previous_value", _jsonb, nullable=True))
    op.add_column(
        "brand_extracted_facts",
        sa.Column("conflict_status", sa.String(length=50), nullable=False, server_default="none"),
    )
    op.add_column("brand_extracted_facts", sa.Column("source_created_at", _ts, nullable=True))
    op.add_column("brand_extracted_facts", sa.Column("import_round", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_brand_extracted_facts_batch_id",
        "brand_extracted_facts",
        "brand_import_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_brand_extracted_facts_batch_id", "brand_extracted_facts", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_brand_extracted_facts_batch_id", table_name="brand_extracted_facts")
    op.drop_constraint("fk_brand_extracted_facts_batch_id", "brand_extracted_facts", type_="foreignkey")
    op.drop_column("brand_extracted_facts", "import_round")
    op.drop_column("brand_extracted_facts", "source_created_at")
    op.drop_column("brand_extracted_facts", "conflict_status")
    op.drop_column("brand_extracted_facts", "previous_value")
    op.drop_column("brand_extracted_facts", "update_mode")
    op.drop_column("brand_extracted_facts", "existing_target_id")
    op.drop_column("brand_extracted_facts", "is_update_suggestion")
    op.drop_column("brand_extracted_facts", "batch_id")

    op.drop_index("ix_brand_source_documents_batch_id", table_name="brand_source_documents")
    op.drop_constraint("fk_brand_source_documents_batch_id", "brand_source_documents", type_="foreignkey")
    op.drop_column("brand_source_documents", "rejected_count")
    op.drop_column("brand_source_documents", "approved_count")
    op.drop_column("brand_source_documents", "needs_review_count")
    op.drop_column("brand_source_documents", "extracted_facts_count")
    op.drop_column("brand_source_documents", "current_step")
    op.drop_column("brand_source_documents", "progress_percent")
    op.drop_column("brand_source_documents", "processing_order")
    op.drop_column("brand_source_documents", "batch_id")

    op.drop_index("ix_brand_import_batches_project_id", table_name="brand_import_batches")
    op.drop_table("brand_import_batches")
