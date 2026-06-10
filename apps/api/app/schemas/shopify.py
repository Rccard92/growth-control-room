from datetime import date, datetime
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
    variants_synced: int = Field(default=0, serialization_alias="variantsSynced")
    orders_synced: int = Field(serialization_alias="ordersSynced")
    line_items_synced: int = Field(default=0, serialization_alias="lineItemsSynced")
    metrics_synced: int = Field(serialization_alias="metricsSynced")
    duration_seconds: float = Field(default=0.0, serialization_alias="durationSeconds")
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


class ShopifyDashboardPeriod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    range: str
    start_date: date = Field(serialization_alias="startDate")
    end_date: date = Field(serialization_alias="endDate")
    timezone: str
    label: str


class ShopifyPeriodMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue: Decimal
    orders_count: int = Field(serialization_alias="ordersCount")
    average_order_value: Decimal = Field(serialization_alias="averageOrderValue")
    paid_orders_count: int = Field(serialization_alias="paidOrdersCount")
    pending_orders_count: int = Field(serialization_alias="pendingOrdersCount")
    fulfilled_orders_count: int = Field(serialization_alias="fulfilledOrdersCount")
    unfulfilled_orders_count: int = Field(serialization_alias="unfulfilledOrdersCount")
    products_without_sales_count: int = Field(
        serialization_alias="productsWithoutSalesCount",
    )


class ShopifyCurrentStateMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    products_count: int = Field(serialization_alias="productsCount")
    active_products_count: int = Field(serialization_alias="activeProductsCount")
    draft_products_count: int = Field(serialization_alias="draftProductsCount")
    low_stock_count: int = Field(serialization_alias="lowStockCount")
    out_of_stock_count: int = Field(serialization_alias="outOfStockCount")
    seo_issues_count: int = Field(serialization_alias="seoIssuesCount")


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
    period_metrics: ShopifyPeriodMetrics = Field(serialization_alias="periodMetrics")
    current_state_metrics: ShopifyCurrentStateMetrics = Field(
        serialization_alias="currentStateMetrics",
    )


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


class ShopifyAttributionBreakdownItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str | None = None
    channel: str | None = None
    campaign: str | None = None
    revenue: Decimal
    orders_count: int = Field(serialization_alias="ordersCount")


class ShopifyNewReturningBySource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str
    new_count: int = Field(serialization_alias="newCount")
    returning_count: int = Field(serialization_alias="returningCount")
    unknown_count: int = Field(serialization_alias="unknownCount")
    revenue: Decimal


class ShopifyTopProductBySource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str
    product_title: str = Field(serialization_alias="productTitle")
    revenue: Decimal
    orders_count: int = Field(serialization_alias="ordersCount")


class ShopifyAttributionIntelligence(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue_by_source: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="revenueBySource",
    )
    orders_by_source: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="ordersBySource",
    )
    revenue_by_channel: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="revenueByChannel",
    )
    orders_by_channel: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="ordersByChannel",
    )
    revenue_by_utm_campaign: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="revenueByUtmCampaign",
    )
    orders_by_utm_campaign: list[ShopifyAttributionBreakdownItem] = Field(
        serialization_alias="ordersByUtmCampaign",
    )
    new_vs_returning_by_source: list[ShopifyNewReturningBySource] = Field(
        serialization_alias="newVsReturningBySource",
    )
    top_products_by_source: list[ShopifyTopProductBySource] = Field(
        serialization_alias="topProductsBySource",
    )
    unattributed_orders_count: int = Field(serialization_alias="unattributedOrdersCount")
    unattributed_revenue: Decimal = Field(serialization_alias="unattributedRevenue")
    direct_orders_count: int = Field(serialization_alias="directOrdersCount")
    unknown_orders_count: int = Field(serialization_alias="unknownOrdersCount")
    tracking_quality_score: float = Field(serialization_alias="trackingQualityScore")


class ShopifyMarketingReportAvailability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shopify_order_attribution_available: bool = Field(
        serialization_alias="shopifyOrderAttributionAvailable",
    )
    shopifyql_available: bool | None = Field(
        default=None,
        serialization_alias="shopifyqlAvailable",
    )
    message: str


class ShopifyDailyDiagnosisItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    severity: str


class ShopifyDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    period: ShopifyDashboardPeriod
    summary: ShopifyDashboardSummary
    alerts: list[ShopifyDashboardAlert]
    product_intelligence: ShopifyProductPerformanceSection = Field(
        serialization_alias="productIntelligence",
    )
    attribution_intelligence: ShopifyAttributionIntelligence = Field(
        serialization_alias="attributionIntelligence",
    )
    inventory_risk: ShopifyInventorySection = Field(serialization_alias="inventoryRisk")
    order_operations: ShopifyOrdersSection = Field(serialization_alias="orderOperations")
    seo_opportunities: ShopifySeoSection = Field(serialization_alias="seoOpportunities")
    daily_diagnosis: list[ShopifyDailyDiagnosisItem] = Field(
        serialization_alias="dailyDiagnosis",
    )
    # Backward compatibility
    product_performance: ShopifyProductPerformanceSection = Field(
        serialization_alias="productPerformance",
    )
    inventory: ShopifyInventorySection
    orders: ShopifyOrdersSection
    seo: ShopifySeoSection
    attribution: ShopifyAttributionReadiness
    marketing_report_availability: ShopifyMarketingReportAvailability = Field(
        serialization_alias="marketingReportAvailability",
    )


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
