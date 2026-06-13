"""Revision ID: 014
Revises: 013
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "shopify_metafield_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("shopify_store_id", sa.UUID(), nullable=False),
        sa.Column("shopify_definition_gid", sa.String(length=255), nullable=False),
        sa.Column("owner_type", sa.String(length=50), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type_name", sa.String(length=100), nullable=False),
        sa.Column("type_category", sa.String(length=100), nullable=True),
        sa.Column("validations", _jsonb, nullable=True),
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
        sa.ForeignKeyConstraint(["shopify_store_id"], ["shopify_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_definition_gid",
            name="uq_shopify_metafield_definitions_store_gid",
        ),
        sa.UniqueConstraint(
            "shopify_store_id",
            "owner_type",
            "namespace",
            "key",
            name="uq_shopify_metafield_definitions_store_owner_ns_key",
        ),
    )
    op.create_index(
        "ix_shopify_metafield_definitions_shopify_store_id",
        "shopify_metafield_definitions",
        ["shopify_store_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_shopify_metafield_definitions_shopify_store_id",
        table_name="shopify_metafield_definitions",
    )
    op.drop_table("shopify_metafield_definitions")
