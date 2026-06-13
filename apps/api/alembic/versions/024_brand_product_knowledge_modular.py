"""Revision ID: 024
Revises: 023
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_product_knowledge_general",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("general_principles", _jsonb, nullable=True),
        sa.Column("common_strengths", _jsonb, nullable=True),
        sa.Column("common_quality_rules", _jsonb, nullable=True),
        sa.Column("common_production_notes", _jsonb, nullable=True),
        sa.Column("common_usage_notes", _jsonb, nullable=True),
        sa.Column("common_objections", _jsonb, nullable=True),
        sa.Column("common_faq", _jsonb, nullable=True),
        sa.Column("communication_rules", _jsonb, nullable=True),
        sa.Column("product_storytelling_rules", _jsonb, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_import_source", sa.String(length=500), nullable=True),
        sa.Column("last_confidence", sa.Float(), nullable=True),
        sa.Column("warnings", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", name="uq_brand_product_knowledge_general_project_id"
        ),
    )
    op.create_index(
        "ix_brand_product_knowledge_general_project_id",
        "brand_product_knowledge_general",
        ["project_id"],
    )

    op.create_table(
        "brand_product_knowledge_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("shopify_product_id", sa.UUID(), nullable=True),
        sa.Column("shopify_product_gid", sa.String(length=255), nullable=True),
        sa.Column("shopify_handle", sa.String(length=255), nullable=True),
        sa.Column("shopify_title", sa.String(length=500), nullable=True),
        sa.Column("product_name", sa.String(length=500), nullable=False),
        sa.Column("product_line", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("strategic_description", sa.Text(), nullable=True),
        sa.Column("origin", sa.Text(), nullable=True),
        sa.Column("ingredients", sa.Text(), nullable=True),
        sa.Column("production_process", sa.Text(), nullable=True),
        sa.Column("taste_notes", sa.Text(), nullable=True),
        sa.Column("color_notes", sa.Text(), nullable=True),
        sa.Column("texture_notes", sa.Text(), nullable=True),
        sa.Column("usage_suggestions", sa.Text(), nullable=True),
        sa.Column("conservation", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("objections", _jsonb, nullable=True),
        sa.Column("faq", _jsonb, nullable=True),
        sa.Column("allowed_claims", _jsonb, nullable=True),
        sa.Column("forbidden_claims", _jsonb, nullable=True),
        sa.Column("seo_notes", sa.Text(), nullable=True),
        sa.Column("ads_social_notes", sa.Text(), nullable=True),
        sa.Column("related_products", _jsonb, nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("last_synced_from_shopify_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["shopify_product_id"], ["shopify_products.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "shopify_product_id",
            name="uq_brand_product_knowledge_items_project_shopify",
        ),
    )
    op.create_index(
        "ix_brand_product_knowledge_items_project_id",
        "brand_product_knowledge_items",
        ["project_id"],
    )
    op.create_index(
        "ix_brand_product_knowledge_items_shopify_product_id",
        "brand_product_knowledge_items",
        ["shopify_product_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_brand_product_knowledge_items_shopify_product_id",
        table_name="brand_product_knowledge_items",
    )
    op.drop_index(
        "ix_brand_product_knowledge_items_project_id",
        table_name="brand_product_knowledge_items",
    )
    op.drop_table("brand_product_knowledge_items")
    op.drop_index(
        "ix_brand_product_knowledge_general_project_id",
        table_name="brand_product_knowledge_general",
    )
    op.drop_table("brand_product_knowledge_general")
