"""Revision ID: 027
Revises: 026
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "content_seo_editorial_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idea"),
        sa.Column("objective", sa.String(length=64), nullable=True),
        sa.Column("primary_keyword", sa.String(length=255), nullable=True),
        sa.Column("secondary_keywords", _jsonb, nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("search_intent", sa.String(length=32), nullable=True),
        sa.Column("commercial_intensity", sa.String(length=32), nullable=True),
        sa.Column("linked_shopify_product_id", sa.UUID(), nullable=True),
        sa.Column("linked_shopify_product_gid", sa.String(length=255), nullable=True),
        sa.Column("linked_shopify_product_title", sa.String(length=500), nullable=True),
        sa.Column("linked_shopify_product_handle", sa.String(length=255), nullable=True),
        sa.Column("linked_collection_id", sa.UUID(), nullable=True),
        sa.Column("linked_collection_title", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("brief_payload", _jsonb, nullable=True),
        sa.Column("article_payload", _jsonb, nullable=True),
        sa.Column("shopify_blog_id", sa.String(length=255), nullable=True),
        sa.Column("shopify_article_id", sa.String(length=255), nullable=True),
        sa.Column("shopify_status", sa.String(length=32), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_content_seo_editorial_items_project_id",
        "content_seo_editorial_items",
        ["project_id"],
    )
    op.create_index(
        "ix_content_seo_editorial_items_planned_date",
        "content_seo_editorial_items",
        ["planned_date"],
    )
    op.create_index(
        "ix_content_seo_editorial_items_status",
        "content_seo_editorial_items",
        ["status"],
    )
    op.create_index(
        "ix_content_seo_editorial_items_content_type",
        "content_seo_editorial_items",
        ["content_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_seo_editorial_items_content_type", "content_seo_editorial_items")
    op.drop_index("ix_content_seo_editorial_items_status", "content_seo_editorial_items")
    op.drop_index("ix_content_seo_editorial_items_planned_date", "content_seo_editorial_items")
    op.drop_index("ix_content_seo_editorial_items_project_id", "content_seo_editorial_items")
    op.drop_table("content_seo_editorial_items")
