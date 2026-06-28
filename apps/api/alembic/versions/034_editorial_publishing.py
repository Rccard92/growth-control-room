"""Revision ID: 034
Revises: 033
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "034"
down_revision: Union[str, None] = "033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())
_ts = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("publishing_payload", _jsonb, nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("shopify_article_gid", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("shopify_article_admin_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("shopify_article_public_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column(
            "publish_status",
            sa.String(length=32),
            nullable=False,
            server_default="not_published",
        ),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("publish_mode", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("scheduled_publish_at", _ts, nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("published_at", _ts, nullable=True),
    )
    op.add_column(
        "content_seo_editorial_items",
        sa.Column("last_publish_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_content_seo_editorial_items_publish_status",
        "content_seo_editorial_items",
        ["publish_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_seo_editorial_items_publish_status",
        table_name="content_seo_editorial_items",
    )
    op.drop_column("content_seo_editorial_items", "last_publish_error")
    op.drop_column("content_seo_editorial_items", "published_at")
    op.drop_column("content_seo_editorial_items", "scheduled_publish_at")
    op.drop_column("content_seo_editorial_items", "publish_mode")
    op.drop_column("content_seo_editorial_items", "publish_status")
    op.drop_column("content_seo_editorial_items", "shopify_article_public_url")
    op.drop_column("content_seo_editorial_items", "shopify_article_admin_url")
    op.drop_column("content_seo_editorial_items", "shopify_article_gid")
    op.drop_column("content_seo_editorial_items", "publishing_payload")
