"""Revision ID: 015
Revises: 014
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("story", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("values", _jsonb, nullable=True),
        sa.Column("differentiators", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_profiles_project_id"),
    )
    op.create_index("ix_brand_profiles_project_id", "brand_profiles", ["project_id"])

    op.create_table(
        "brand_voices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("tone", sa.String(length=255), nullable=True),
        sa.Column("style_notes", sa.Text(), nullable=True),
        sa.Column("formality_level", sa.String(length=50), nullable=True),
        sa.Column("emoji_policy", sa.String(length=100), nullable=True),
        sa.Column("words_to_use", _jsonb, nullable=True),
        sa.Column("words_to_avoid", _jsonb, nullable=True),
        sa.Column("examples_good", _jsonb, nullable=True),
        sa.Column("examples_bad", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_voices_project_id"),
    )
    op.create_index("ix_brand_voices_project_id", "brand_voices", ["project_id"])

    op.create_table(
        "brand_product_knowledge",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False, server_default="product"),
        sa.Column("shopify_gid", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ingredients", sa.Text(), nullable=True),
        sa.Column("origin", sa.String(length=255), nullable=True),
        sa.Column("production_process", sa.Text(), nullable=True),
        sa.Column("usage_suggestions", sa.Text(), nullable=True),
        sa.Column("conservation", sa.Text(), nullable=True),
        sa.Column("taste_notes", sa.Text(), nullable=True),
        sa.Column("objections", _jsonb, nullable=True),
        sa.Column("faq", _jsonb, nullable=True),
        sa.Column("claims_allowed", _jsonb, nullable=True),
        sa.Column("claims_forbidden", _jsonb, nullable=True),
        sa.Column("related_products", _jsonb, nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_product_knowledge_project_id", "brand_product_knowledge", ["project_id"])

    op.create_table(
        "brand_audience_insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("segment_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("motivations", _jsonb, nullable=True),
        sa.Column("pain_points", _jsonb, nullable=True),
        sa.Column("objections", _jsonb, nullable=True),
        sa.Column("questions", _jsonb, nullable=True),
        sa.Column("buying_triggers", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_audience_insights_project_id", "brand_audience_insights", ["project_id"])

    op.create_table(
        "brand_claim_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("examples", _jsonb, nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_claim_rules_project_id", "brand_claim_rules", ["project_id"])

    op.create_table(
        "brand_seo_strategies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("primary_keywords", _jsonb, nullable=True),
        sa.Column("secondary_keywords", _jsonb, nullable=True),
        sa.Column("keyword_clusters", _jsonb, nullable=True),
        sa.Column("priority_pages", _jsonb, nullable=True),
        sa.Column("internal_linking_notes", sa.Text(), nullable=True),
        sa.Column("meta_title_pattern", sa.String(length=500), nullable=True),
        sa.Column("meta_description_pattern", sa.String(length=500), nullable=True),
        sa.Column("url_handle_pattern", sa.String(length=500), nullable=True),
        sa.Column("competitors", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_brand_seo_strategies_project_id"),
    )
    op.create_index("ix_brand_seo_strategies_project_id", "brand_seo_strategies", ["project_id"])

    op.create_table(
        "brand_content_pillars",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("products", _jsonb, nullable=True),
        sa.Column("channels", _jsonb, nullable=True),
        sa.Column("example_topics", _jsonb, nullable=True),
        sa.Column("cta_notes", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_content_pillars_project_id", "brand_content_pillars", ["project_id"])

    op.create_table(
        "brand_ai_guardrails",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("applies_to", _jsonb, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_ai_guardrails_project_id", "brand_ai_guardrails", ["project_id"])

    op.create_table(
        "brand_assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("file_url", sa.String(length=1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_assets_project_id", "brand_assets", ["project_id"])


def downgrade() -> None:
    op.drop_table("brand_assets")
    op.drop_table("brand_ai_guardrails")
    op.drop_table("brand_content_pillars")
    op.drop_table("brand_seo_strategies")
    op.drop_table("brand_claim_rules")
    op.drop_table("brand_audience_insights")
    op.drop_table("brand_product_knowledge")
    op.drop_table("brand_voices")
    op.drop_table("brand_profiles")
