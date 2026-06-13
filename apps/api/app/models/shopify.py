import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.integration import Integration
    from app.models.project import Project


class ShopifyStore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_stores"
    __table_args__ = (
        UniqueConstraint("integration_id", name="uq_shopify_stores_integration_id"),
        UniqueConstraint("project_id", "shop_domain", name="uq_shopify_stores_project_id_shop_domain"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
    )
    shop_domain: Mapped[str] = mapped_column(String(255))
    shop_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    connection_status: Mapped[str] = mapped_column(String(20), default="disconnected")
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    granted_scopes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    scopes_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    project: Mapped["Project"] = relationship(back_populates="shopify_stores")
    integration: Mapped["Integration"] = relationship()
    products: Mapped[list["ShopifyProduct"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["ShopifyOrder"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    daily_metrics: Mapped[list["ShopifyDailyMetric"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    collections: Mapped[list["ShopifyCollection"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    pages: Mapped[list["ShopifyPage"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    blogs: Mapped[list["ShopifyBlog"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )
    articles: Mapped[list["ShopifyArticle"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
    )


class ShopifyProduct(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_products"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_products_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_inventory: Mapped[int | None] = mapped_column(Integer, nullable=True)
    featured_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_images: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at_shopify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at_shopify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    variants_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="products")
    variants: Mapped[list["ShopifyProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    metafields: Mapped[list["ShopifyProductMetafield"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ShopifyProductMetafield(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_product_metafields"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_metafield_gid",
            name="uq_shopify_product_metafields_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_products.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_metafield_gid: Mapped[str] = mapped_column(String(255))
    namespace: Mapped[str] = mapped_column(String(255))
    key: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(100))
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    definition_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    product: Mapped["ShopifyProduct"] = relationship(back_populates="metafields")


class ShopifyProductVariant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_product_variants"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_variant_gid",
            name="uq_shopify_product_variants_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_products.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_variant_gid: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    inventory_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_options: Mapped[list[dict[str, str]] | None] = mapped_column(JSONB, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    product: Mapped["ShopifyProduct"] = relationship(back_populates="variants")


class ShopifyOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_orders"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_gid",
            name="uq_shopify_orders_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_gid: Mapped[str] = mapped_column(String(255))
    order_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at_shopify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    financial_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    subtotal_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    current_total_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_discounts: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    refund_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    refund_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registered_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    channel_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    landing_page: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referrer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_landing_page: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_referral_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discount_codes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    attribution_ready: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    days_to_conversion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="orders")
    line_items: Mapped[list["ShopifyOrderLineItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    refunds: Mapped[list["ShopifyOrderRefund"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class ShopifyOrderRefund(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_order_refunds"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_refund_gid",
            name="uq_shopify_order_refunds_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_orders.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_refund_gid: Mapped[str] = mapped_column(String(255))
    refund_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    order: Mapped["ShopifyOrder"] = relationship(back_populates="refunds")


class ShopifyOrderLineItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_order_line_items"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "shopify_line_item_gid",
            name="uq_shopify_order_line_items_store_gid",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_orders.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_line_item_gid: Mapped[str] = mapped_column(String(255))
    product_gid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    variant_gid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    original_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discounted_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    order: Mapped["ShopifyOrder"] = relationship(back_populates="line_items")


class ShopifyDailyMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "shopify_store_id",
            "date",
            name="uq_shopify_daily_metrics_store_date",
        ),
    )

    shopify_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    date: Mapped[date] = mapped_column(Date)
    orders_count: Mapped[int] = mapped_column(Integer, default=0)
    gross_sales: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    net_sales: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    average_order_value: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    store: Mapped["ShopifyStore"] = relationship(back_populates="daily_metrics")
