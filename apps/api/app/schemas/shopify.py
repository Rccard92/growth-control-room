from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShopifyConnectRequest(BaseModel):
    shop_domain: str = Field(min_length=1)
    admin_access_token: str = Field(min_length=1)


class ShopifyConnectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    connected: bool
    shop_domain: str = Field(serialization_alias="shopDomain")
    shop_name: str | None = Field(default=None, serialization_alias="shopName")
    connection_status: str = Field(serialization_alias="connectionStatus")


class ShopifyStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    connected: bool
    shop_domain: str | None = Field(default=None, serialization_alias="shopDomain")
    shop_name: str | None = Field(default=None, serialization_alias="shopName")
    last_sync_at: datetime | None = Field(default=None, serialization_alias="lastSyncAt")


class ShopifySyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_synced: int = Field(serialization_alias="productsSynced")
    orders_synced: int = Field(serialization_alias="ordersSynced")
    metrics_synced: int = Field(serialization_alias="metricsSynced")
    last_sync_at: datetime = Field(serialization_alias="lastSyncAt")


class ShopifyTopProduct(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_gid: str = Field(serialization_alias="productGid")
    title: str
    quantity_sold: int = Field(serialization_alias="quantitySold")


class ShopifyProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    title: str
    handle: str | None = None
    status: str | None = None
    total_inventory: int | None = Field(default=None, serialization_alias="totalInventory")
    featured_image_url: str | None = Field(default=None, serialization_alias="featuredImageUrl")


class ShopifyOrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    order_name: str | None = Field(default=None, serialization_alias="orderName")
    created_at_shopify: datetime | None = Field(
        default=None,
        serialization_alias="createdAtShopify",
    )
    financial_status: str | None = Field(default=None, serialization_alias="financialStatus")
    fulfillment_status: str | None = Field(
        default=None,
        serialization_alias="fulfillmentStatus",
    )
    total_price: Decimal = Field(serialization_alias="totalPrice")
    currency: str | None = None
    customer_email: str | None = Field(default=None, serialization_alias="customerEmail")


class ShopifyDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue: Decimal
    orders_count: int = Field(serialization_alias="ordersCount")
    average_order_value: Decimal = Field(serialization_alias="averageOrderValue")
    products_count: int = Field(serialization_alias="productsCount")
    low_stock_products: list[ShopifyProductSummary] = Field(
        serialization_alias="lowStockProducts",
    )
    top_products: list[ShopifyTopProduct] = Field(serialization_alias="topProducts")
    recent_orders: list[ShopifyOrderSummary] = Field(serialization_alias="recentOrders")
    last_sync_at: datetime | None = Field(default=None, serialization_alias="lastSyncAt")


class ShopifyProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    title: str
    handle: str | None = None
    status: str | None = None
    vendor: str | None = None
    product_type: str | None = Field(default=None, serialization_alias="productType")
    total_inventory: int | None = Field(default=None, serialization_alias="totalInventory")
    featured_image_url: str | None = Field(default=None, serialization_alias="featuredImageUrl")
    seo_title: str | None = Field(default=None, serialization_alias="seoTitle")
    seo_description: str | None = Field(default=None, serialization_alias="seoDescription")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ShopifyOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    shopify_gid: str = Field(serialization_alias="shopifyGid")
    order_name: str | None = Field(default=None, serialization_alias="orderName")
    created_at_shopify: datetime | None = Field(
        default=None,
        serialization_alias="createdAtShopify",
    )
    processed_at: datetime | None = Field(default=None, serialization_alias="processedAt")
    financial_status: str | None = Field(default=None, serialization_alias="financialStatus")
    fulfillment_status: str | None = Field(
        default=None,
        serialization_alias="fulfillmentStatus",
    )
    total_price: Decimal = Field(serialization_alias="totalPrice")
    subtotal_price: Decimal | None = Field(default=None, serialization_alias="subtotalPrice")
    currency: str | None = None
    customer_email: str | None = Field(default=None, serialization_alias="customerEmail")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
