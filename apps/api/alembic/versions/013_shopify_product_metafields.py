"""Revision ID: 013
Revises: 012
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "shopify_product_metafields",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("shopify_store_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("shopify_metafield_gid", sa.String(length=255), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("definition_name", sa.String(length=500), nullable=True),
        sa.Column("definition_description", sa.Text(), nullable=True),
        sa.Column("raw_payload", _jsonb, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["shopify_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_metafield_gid",
            name="uq_shopify_product_metafields_store_gid",
        ),
    )
    op.create_index(
        "ix_shopify_product_metafields_product_id",
        "shopify_product_metafields",
        ["product_id"],
    )
    op.create_index(
        "ix_shopify_product_metafields_shopify_store_id",
        "shopify_product_metafields",
        ["shopify_store_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_shopify_product_metafields_shopify_store_id", "shopify_product_metafields")
    op.drop_index("ix_shopify_product_metafields_product_id", "shopify_product_metafields")
    op.drop_table("shopify_product_metafields")
