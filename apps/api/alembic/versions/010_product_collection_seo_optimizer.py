"""product collection seo optimizer tables

Revision ID: 010
Revises: 009
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ts = sa.DateTime(timezone=True)
_uuid = postgresql.UUID(as_uuid=True)
_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column("shopify_products", sa.Column("description_html", sa.Text(), nullable=True))
    op.add_column("shopify_products", sa.Column("description_text", sa.Text(), nullable=True))
    op.add_column("shopify_products", sa.Column("media_images", _jsonb, nullable=True))
    op.add_column(
        "shopify_collections",
        sa.Column("image_alt", sa.String(length=500), nullable=True),
    )

    op.create_table(
        "seo_entity_analyses",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", _uuid, nullable=False),
        sa.Column("entity_gid", sa.String(length=255), nullable=False),
        sa.Column("entity_title", sa.String(length=500), nullable=False),
        sa.Column("score_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_title", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_seo_title", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_meta_description", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_description", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_image_alt", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_handle", sa.Integer(), server_default="0", nullable=False),
        sa.Column("score_tags", sa.Integer(), server_default="0", nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="warning", nullable=False),
        sa.Column("issues", _jsonb, nullable=True),
        sa.Column("recommendations", _jsonb, nullable=True),
        sa.Column("last_analyzed_at", _ts, nullable=True),
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
            name="uq_seo_entity_analyses_entity",
        ),
    )
    op.create_index("ix_seo_entity_analyses_project_id", "seo_entity_analyses", ["project_id"])
    op.create_index(
        "ix_seo_entity_analyses_shopify_store_id",
        "seo_entity_analyses",
        ["shopify_store_id"],
    )
    op.create_index("ix_seo_entity_analyses_entity_id", "seo_entity_analyses", ["entity_id"])

    op.create_table(
        "seo_optimization_proposals",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", _uuid, nullable=False),
        sa.Column("entity_gid", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("source", sa.String(length=20), server_default="rules", nullable=False),
        sa.Column("current_values", _jsonb, nullable=True),
        sa.Column("proposed_values", _jsonb, nullable=True),
        sa.Column("reasoning", _jsonb, nullable=True),
        sa.Column("risk_level", sa.String(length=20), server_default="low", nullable=False),
        sa.Column("approved_at", _ts, nullable=True),
        sa.Column("applied_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_seo_optimization_proposals_project_id",
        "seo_optimization_proposals",
        ["project_id"],
    )
    op.create_index(
        "ix_seo_optimization_proposals_shopify_store_id",
        "seo_optimization_proposals",
        ["shopify_store_id"],
    )
    op.create_index(
        "ix_seo_optimization_proposals_entity_id",
        "seo_optimization_proposals",
        ["entity_id"],
    )

    op.create_table(
        "seo_change_logs",
        sa.Column("id", _uuid, nullable=False),
        sa.Column("project_id", _uuid, nullable=False),
        sa.Column("shopify_store_id", _uuid, nullable=False),
        sa.Column("proposal_id", _uuid, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_gid", sa.String(length=255), nullable=False),
        sa.Column("applied_values", _jsonb, nullable=True),
        sa.Column("shopify_response", _jsonb, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", _ts, server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["proposal_id"],
            ["seo_optimization_proposals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seo_change_logs_project_id", "seo_change_logs", ["project_id"])
    op.create_index("ix_seo_change_logs_proposal_id", "seo_change_logs", ["proposal_id"])


def downgrade() -> None:
    op.drop_table("seo_change_logs")
    op.drop_table("seo_optimization_proposals")
    op.drop_table("seo_entity_analyses")
    op.drop_column("shopify_collections", "image_alt")
    op.drop_column("shopify_products", "media_images")
    op.drop_column("shopify_products", "description_text")
    op.drop_column("shopify_products", "description_html")
