"""shopify sync v2 tables and columns

Revision ID: 007
Revises: 006
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shopify_products",
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "shopify_products",
        sa.Column("created_at_shopify", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "shopify_products",
        sa.Column("updated_at_shopify", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "shopify_products",
        sa.Column("variants_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "shopify_products",
        sa.Column("min_price", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "shopify_products",
        sa.Column("max_price", sa.Numeric(precision=12, scale=2), nullable=True),
    )

    op.add_column(
        "shopify_orders",
        sa.Column("registered_source_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("channel_handle", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column(
            "current_total_price",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("total_discounts", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("shipping_price", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("discount_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("attribution_ready", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("days_to_conversion", sa.Integer(), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("customer_order_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_utm_source", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_utm_medium", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_utm_campaign", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_utm_content", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_utm_term", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_landing_page", sa.Text(), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_referral_code", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_source", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "shopify_orders",
        sa.Column("first_source_type", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "shopify_product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_variant_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("compare_at_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("inventory_quantity", sa.Integer(), nullable=True),
        sa.Column(
            "selected_options",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
            ["product_id"],
            ["shopify_products.id"],
            name=op.f("fk_shopify_product_variants_product_id_shopify_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_product_variants_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_product_variants")),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_variant_gid",
            name="uq_shopify_product_variants_store_gid",
        ),
    )
    op.create_index(
        op.f("ix_shopify_product_variants_shopify_store_id"),
        "shopify_product_variants",
        ["shopify_store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopify_product_variants_product_id"),
        "shopify_product_variants",
        ["product_id"],
        unique=False,
    )

    op.create_table(
        "shopify_order_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_line_item_gid", sa.String(length=255), nullable=False),
        sa.Column("product_gid", sa.String(length=255), nullable=True),
        sa.Column("variant_gid", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("product_type", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("original_total", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("discounted_total", sa.Numeric(precision=12, scale=2), nullable=True),
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
            name=op.f("fk_shopify_order_line_items_order_id_shopify_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_order_line_items_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_order_line_items")),
        sa.UniqueConstraint(
            "shopify_store_id",
            "shopify_line_item_gid",
            name="uq_shopify_order_line_items_store_gid",
        ),
    )
    op.create_index(
        op.f("ix_shopify_order_line_items_shopify_store_id"),
        "shopify_order_line_items",
        ["shopify_store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shopify_order_line_items_order_id"),
        "shopify_order_line_items",
        ["order_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_shopify_order_line_items_order_id"),
        table_name="shopify_order_line_items",
    )
    op.drop_index(
        op.f("ix_shopify_order_line_items_shopify_store_id"),
        table_name="shopify_order_line_items",
    )
    op.drop_table("shopify_order_line_items")

    op.drop_index(
        op.f("ix_shopify_product_variants_product_id"),
        table_name="shopify_product_variants",
    )
    op.drop_index(
        op.f("ix_shopify_product_variants_shopify_store_id"),
        table_name="shopify_product_variants",
    )
    op.drop_table("shopify_product_variants")

    op.drop_column("shopify_orders", "first_source_type")
    op.drop_column("shopify_orders", "first_source")
    op.drop_column("shopify_orders", "first_referral_code")
    op.drop_column("shopify_orders", "first_landing_page")
    op.drop_column("shopify_orders", "first_utm_term")
    op.drop_column("shopify_orders", "first_utm_content")
    op.drop_column("shopify_orders", "first_utm_campaign")
    op.drop_column("shopify_orders", "first_utm_medium")
    op.drop_column("shopify_orders", "first_utm_source")
    op.drop_column("shopify_orders", "customer_order_index")
    op.drop_column("shopify_orders", "days_to_conversion")
    op.drop_column("shopify_orders", "attribution_ready")
    op.drop_column("shopify_orders", "discount_codes")
    op.drop_column("shopify_orders", "shipping_price")
    op.drop_column("shopify_orders", "total_discounts")
    op.drop_column("shopify_orders", "current_total_price")
    op.drop_column("shopify_orders", "channel_handle")
    op.drop_column("shopify_orders", "registered_source_url")

    op.drop_column("shopify_products", "max_price")
    op.drop_column("shopify_products", "min_price")
    op.drop_column("shopify_products", "variants_count")
    op.drop_column("shopify_products", "updated_at_shopify")
    op.drop_column("shopify_products", "created_at_shopify")
    op.drop_column("shopify_products", "tags")
