"""shopify tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shopify_stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_domain", sa.String(length=255), nullable=False),
        sa.Column("shop_name", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=True),
        sa.Column(
            "connection_status",
            sa.String(length=20),
            server_default="disconnected",
            nullable=False,
        ),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["integration_id"],
            ["integrations.id"],
            name=op.f("fk_shopify_stores_integration_id_integrations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_shopify_stores_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_stores")),
        sa.UniqueConstraint("integration_id", name="uq_shopify_stores_integration_id"),
        sa.UniqueConstraint("project_id", "shop_domain", name="uq_shopify_stores_project_id_shop_domain"),
    )
    op.create_index(op.f("ix_shopify_stores_project_id"), "shopify_stores", ["project_id"], unique=False)

    op.create_table(
        "shopify_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("vendor", sa.String(length=255), nullable=True),
        sa.Column("product_type", sa.String(length=255), nullable=True),
        sa.Column("total_inventory", sa.Integer(), nullable=True),
        sa.Column("featured_image_url", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(length=500), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_products_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_products")),
        sa.UniqueConstraint("shopify_store_id", "shopify_gid", name="uq_shopify_products_store_gid"),
    )
    op.create_index(
        op.f("ix_shopify_products_shopify_store_id"),
        "shopify_products",
        ["shopify_store_id"],
        unique=False,
    )

    op.create_table(
        "shopify_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_gid", sa.String(length=255), nullable=False),
        sa.Column("order_name", sa.String(length=100), nullable=True),
        sa.Column("created_at_shopify", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("financial_status", sa.String(length=50), nullable=True),
        sa.Column("fulfillment_status", sa.String(length=50), nullable=True),
        sa.Column("total_price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("subtotal_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_orders_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_orders")),
        sa.UniqueConstraint("shopify_store_id", "shopify_gid", name="uq_shopify_orders_store_gid"),
    )
    op.create_index(
        op.f("ix_shopify_orders_shopify_store_id"),
        "shopify_orders",
        ["shopify_store_id"],
        unique=False,
    )

    op.create_table(
        "shopify_daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopify_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("orders_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("gross_sales", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("net_sales", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("average_order_value", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["shopify_store_id"],
            ["shopify_stores.id"],
            name=op.f("fk_shopify_daily_metrics_shopify_store_id_shopify_stores"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopify_daily_metrics")),
        sa.UniqueConstraint("shopify_store_id", "date", name="uq_shopify_daily_metrics_store_date"),
    )
    op.create_index(
        op.f("ix_shopify_daily_metrics_shopify_store_id"),
        "shopify_daily_metrics",
        ["shopify_store_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shopify_daily_metrics_shopify_store_id"), table_name="shopify_daily_metrics")
    op.drop_table("shopify_daily_metrics")
    op.drop_index(op.f("ix_shopify_orders_shopify_store_id"), table_name="shopify_orders")
    op.drop_table("shopify_orders")
    op.drop_index(op.f("ix_shopify_products_shopify_store_id"), table_name="shopify_products")
    op.drop_table("shopify_products")
    op.drop_index(op.f("ix_shopify_stores_project_id"), table_name="shopify_stores")
    op.drop_table("shopify_stores")
