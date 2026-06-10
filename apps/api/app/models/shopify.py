import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.integration import Integration


class ShopifyStore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_stores"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        unique=True,
    )
    shop_domain: Mapped[str] = mapped_column(String(255))
    shop_name: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    timezone: Mapped[str] = mapped_column(String(100), default="Europe/Rome")
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    integration: Mapped["Integration"] = relationship(back_populates="shopify_store")
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
            "store_id",
            "shopify_product_id",
            name="uq_shopify_products_store_id_shopify_product_id",
        ),
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_product_id: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="active")
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    store: Mapped["ShopifyStore"] = relationship(back_populates="products")


class ShopifyOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_orders"
    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "shopify_order_id",
            name="uq_shopify_orders_store_id_shopify_order_id",
        ),
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    shopify_order_id: Mapped[str] = mapped_column(String(50))
    order_number: Mapped[str] = mapped_column(String(50))
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    financial_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fulfillment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ordered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    store: Mapped["ShopifyStore"] = relationship(back_populates="orders")


class ShopifyDailyMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shopify_daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "date",
            name="uq_shopify_daily_metrics_store_id_date",
        ),
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shopify_stores.id", ondelete="CASCADE"),
        index=True,
    )
    date: Mapped[date] = mapped_column(Date)
    orders_count: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    store: Mapped["ShopifyStore"] = relationship(back_populates="daily_metrics")
