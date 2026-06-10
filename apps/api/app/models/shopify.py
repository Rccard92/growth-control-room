import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
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
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="products")


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
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="orders")


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
