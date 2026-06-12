"""shopify order refunds and tax columns

Revision ID: 008
Revises: 007
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shopify_orders",
        sa.Column("total_tax", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("refund_total", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("refund_count", sa.Integer(), nullable=True),
    )

    op.create_table(
        "shopify_order_refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_refund_gid", sa.String(length=255), nullable=False),
        sa.Column("refund_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["shopify_orders.id"],
            name=op.f("fk_shopify_order_refunds_order_id_shopify_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_order_refunds_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_order_refunds")),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_refund_gid",
            name="uq_shopify_order_refunds_store_gid",
        ),
    )
    op.create_index(
        op.f("ix_shopify_order_refunds_shopify_store_id"),
        "shopify_order_refunds",
        ["shopify_store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopify_order_refunds_order_id"),
        "shopify_order_refunds",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopify_order_refunds_refund_created_at"),
        "shopify_order_refunds",
        ["refund_created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_shopify_order_refunds_refund_created_at"),
        table_name="shopify_order_refunds",
    )
    op.drop_index(
        op.f("ix_shopify_order_refunds_order_id"),
        table_name="shopify_order_refunds",
    )
    op.drop_index(
        op.f("ix_shopify_order_refunds_shopify_store_id"),
        table_name="shopify_order_refunds",
    )
    op.drop_table("shopify_order_refunds")

    op.drop_column("shopify_orders", "refund_count")
    op.drop_column("shopify_orders", "refund_total")
    op.drop_column("shopify_orders", "total_tax")
