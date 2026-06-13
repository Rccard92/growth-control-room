"""Revision ID: 016
Revises: 015
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_source_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_mode", sa.String(length=50), nullable=False, server_default="text_only"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=True),
        sa.Column("document_summary", sa.Text(), nullable=True),
        sa.Column("extraction_status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("uploaded_at", _ts, nullable=False),
        sa.Column("processed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_brand_source_documents_project_id",
        "brand_source_documents",
        ["project_id"],
    )

    op.create_table(
        "brand_extracted_facts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("source_document_id", sa.UUID(), nullable=True),
        sa.Column("target_section", sa.String(length=100), nullable=False),
        sa.Column("target_entity_type", sa.String(length=50), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("extracted_value", _jsonb, nullable=True),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="suggested"),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column("reviewed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["brand_source_documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_brand_extracted_facts_project_id",
        "brand_extracted_facts",
        ["project_id"],
    )
    op.create_index(
        "ix_brand_extracted_facts_source_document_id",
        "brand_extracted_facts",
        ["source_document_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_brand_extracted_facts_source_document_id", table_name="brand_extracted_facts")
    op.drop_index("ix_brand_extracted_facts_project_id", table_name="brand_extracted_facts")
    op.drop_table("brand_extracted_facts")
    op.drop_index("ix_brand_source_documents_project_id", table_name="brand_source_documents")
    op.drop_table("brand_source_documents")
