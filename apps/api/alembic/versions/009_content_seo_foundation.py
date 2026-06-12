"""content seo engine foundation tables

Revision ID: 009
Revises: 008
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)
_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "shopify_collections",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(length=500), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("products_count", sa.Integer(), nullable=True),
        sa.Column("raw_payload", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_collections_store_gid",
        ),
    )
    op.create_index("ix_shopify_collections_shopify_store_id", "shopify_collections", ["shopify_store_id"])

    op.create_table(
        "shopify_pages",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(length=500), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("published_at_shopify", _ts, nullable=True),
        sa.Column("raw_payload", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_pages_store_gid",
        ),
    )
    op.create_index("ix_shopify_pages_shopify_store_id", "shopify_pages", ["shopify_store_id"])

    op.create_table(
        "shopify_blogs",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_blogs_store_gid",
        ),
    )
    op.create_index("ix_shopify_blogs_shopify_store_id", "shopify_blogs", ["shopify_store_id"])

    op.create_table(
        "shopify_articles",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("blog_id", _uuid, nullable=True),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("summary_html", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(length=500), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("tags", _jsonb, nullable=True),
        sa.Column("published_at_shopify", _ts, nullable=True),
        sa.Column("raw_payload", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["blog_id"], ["shopify_blogs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_articles_store_gid",
        ),
    )
    op.create_index("ix_shopify_articles_shopify_store_id", "shopify_articles", ["shopify_store_id"])
    op.create_index("ix_shopify_articles_blog_id", "shopify_articles", ["blog_id"])

    op.create_table(
        "seo_audit_issues",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", _uuid, nullable=False),
        sa.Column("issue_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "shopify_store_id",
            "entity_type",
            "entity_id",
            "issue_type",
            name="uq_seo_audit_issues_dedup",
        ),
    )
    op.create_index("ix_seo_audit_issues_project_id", "seo_audit_issues", ["project_id"])
    op.create_index("ix_seo_audit_issues_shopify_store_id", "seo_audit_issues", ["shopify_store_id"])

    op.create_table(
        "content_opportunities",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("opportunity_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_entity_type", sa.String(length=50), nullable=True),
        sa.Column("target_entity_id", _uuid, nullable=True),
        sa.Column("suggested_keyword", sa.String(length=255), nullable=True),
        sa.Column("search_intent", sa.String(length=50), nullable=True),
        sa.Column("suggested_products", _jsonb, nullable=True),
        sa.Column("suggested_collections", _jsonb, nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "shopify_store_id",
            "opportunity_type",
            "title",
            "target_entity_id",
            name="uq_content_opportunities_dedup",
        ),
    )
    op.create_index("ix_content_opportunities_project_id", "content_opportunities", ["project_id"])
    op.create_index(
        "ix_content_opportunities_shopify_store_id",
        "content_opportunities",
        ["shopify_store_id"],
    )

    op.create_table(
        "content_briefs",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("opportunity_id", _uuid, nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("primary_keyword", sa.String(length=255), nullable=True),
        sa.Column("secondary_keywords", _jsonb, nullable=True),
        sa.Column("search_intent", sa.String(length=50), nullable=True),
        sa.Column("outline", _jsonb, nullable=True),
        sa.Column("internal_links", _jsonb, nullable=True),
        sa.Column("products_to_feature", _jsonb, nullable=True),
        sa.Column("faq", _jsonb, nullable=True),
        sa.Column("cta", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["content_opportunities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_briefs_project_id", "content_briefs", ["project_id"])
    op.create_index("ix_content_briefs_shopify_store_id", "content_briefs", ["shopify_store_id"])


def downgrade() -> None:
    op.drop_table("content_briefs")
    op.drop_table("content_opportunities")
    op.drop_table("seo_audit_issues")
    op.drop_table("shopify_articles")
    op.drop_table("shopify_blogs")
    op.drop_table("shopify_pages")
    op.drop_table("shopify_collections")
