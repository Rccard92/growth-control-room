from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShopifyOAuthStartResponse(BaseModel):
    authorization_url: str = Field(serialization_alias="authorizationUrl")


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


class ShopifyDashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue: Decimal
    orders_count: int = Field(serialization_alias="ordersCount")
    average_order_value: Decimal = Field(serialization_alias="averageOrderValue")
    products_count: int = Field(serialization_alias="productsCount")
    active_products_count: int = Field(serialization_alias="activeProductsCount")
    draft_products_count: int = Field(serialization_alias="draftProductsCount")
    paid_orders_count: int = Field(serialization_alias="paidOrdersCount")
    pending_orders_count: int = Field(serialization_alias="pendingOrdersCount")
    fulfilled_orders_count: int = Field(serialization_alias="fulfilledOrdersCount")
    unfulfilled_orders_count: int = Field(serialization_alias="unfulfilledOrdersCount")
    low_stock_count: int = Field(serialization_alias="lowStockCount")
    out_of_stock_count: int = Field(serialization_alias="outOfStockCount")
    products_without_sales_count: int = Field(serialization_alias="productsWithoutSalesCount")
    seo_issues_count: int = Field(serialization_alias="seoIssuesCount")
    critical_alerts_count: int = Field(serialization_alias="criticalAlertsCount")
    last_sync_at: datetime | None = Field(default=None, serialization_alias="lastSyncAt")
    shop_domain: str = Field(serialization_alias="shopDomain")


class ShopifyDashboardProduct(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    status: str | None = None
    total_inventory: int | None = Field(default=None, serialization_alias="totalInventory")
    featured_image_url: str | None = Field(default=None, serialization_alias="featuredImageUrl")
    product_type: str | None = Field(default=None, serialization_alias="productType")
    vendor: str | None = None
    handle: str | None = None


class ShopifyDashboardOrder(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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


class ShopifyDashboardAlert(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    severity: str
    title: str
    description: str
    entity_type: str = Field(serialization_alias="entityType")
    entity_id: str | None = Field(default=None, serialization_alias="entityId")
    action_label: str | None = Field(default=None, serialization_alias="actionLabel")


class ShopifyBestSellerPerformance(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    sku: str | None = None
    quantity_sold: int = Field(serialization_alias="quantitySold")
    revenue: Decimal
    current_inventory: int | None = Field(default=None, serialization_alias="currentInventory")
    status: str | None = None


class ShopifyNoSalesProduct(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    current_inventory: int | None = Field(default=None, serialization_alias="currentInventory")
    status: str | None = None
    product_type: str | None = Field(default=None, serialization_alias="productType")
    seo_issue: bool = Field(default=False, serialization_alias="seoIssue")


class ShopifyHighStockLowSales(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    current_inventory: int | None = Field(default=None, serialization_alias="currentInventory")
    quantity_sold: int = Field(serialization_alias="quantitySold")
    issue: str


class ShopifyProductPerformanceSection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    best_sellers: list[ShopifyBestSellerPerformance] = Field(serialization_alias="bestSellers")
    no_sales_products: list[ShopifyNoSalesProduct] = Field(serialization_alias="noSalesProducts")
    high_stock_low_sales: list[ShopifyHighStockLowSales] = Field(
        serialization_alias="highStockLowSales",
    )


class ShopifyInventorySummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_units: int = Field(serialization_alias="totalUnits")
    active_products: int = Field(serialization_alias="activeProducts")
    zero_stock_active_products: int = Field(serialization_alias="zeroStockActiveProducts")
    low_stock_active_products: int = Field(serialization_alias="lowStockActiveProducts")


class ShopifyInventorySection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    low_stock_products: list[ShopifyDashboardProduct] = Field(
        serialization_alias="lowStockProducts",
    )
    out_of_stock_products: list[ShopifyDashboardProduct] = Field(
        serialization_alias="outOfStockProducts",
    )
    inventory_summary: ShopifyInventorySummary = Field(serialization_alias="inventorySummary")


class ShopifyOrdersSection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    recent_orders: list[ShopifyDashboardOrder] = Field(serialization_alias="recentOrders")
    pending_orders: list[ShopifyDashboardOrder] = Field(serialization_alias="pendingOrders")
    unfulfilled_orders: list[ShopifyDashboardOrder] = Field(
        serialization_alias="unfulfilledOrders",
    )


class ShopifySeoOpportunity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    issue: str
    priority: str


class ShopifySeoSection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_missing_meta_title: list[ShopifyDashboardProduct] = Field(
        serialization_alias="productsMissingMetaTitle",
    )
    products_missing_meta_description: list[ShopifyDashboardProduct] = Field(
        serialization_alias="productsMissingMetaDescription",
    )
    products_missing_both: list[ShopifyDashboardProduct] = Field(
        serialization_alias="productsMissingBoth",
    )
    seo_opportunities: list[ShopifySeoOpportunity] = Field(serialization_alias="seoOpportunities")


class ShopifyAttributionReadiness(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    connected_sources: list[str] = Field(serialization_alias="connectedSources")
    channel_breakdown: list[dict[str, Any]] = Field(serialization_alias="channelBreakdown")
    utm_coverage: float | None = Field(default=None, serialization_alias="utmCoverage")
    message: str


class ShopifyDailyDiagnosisItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    severity: str


class ShopifyDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: ShopifyDashboardSummary
    alerts: list[ShopifyDashboardAlert]
    product_performance: ShopifyProductPerformanceSection = Field(
        serialization_alias="productPerformance",
    )
    inventory: ShopifyInventorySection
    orders: ShopifyOrdersSection
    seo: ShopifySeoSection
    attribution: ShopifyAttributionReadiness
    daily_diagnosis: list[ShopifyDailyDiagnosisItem] = Field(serialization_alias="dailyDiagnosis")


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
