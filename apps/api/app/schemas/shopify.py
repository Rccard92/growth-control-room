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


class ShopifyScopesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shop_domain: str = Field(serialization_alias="shopDomain")
    configured_scopes: list[str] = Field(serialization_alias="configuredScopes")
    granted_scopes: list[str] = Field(serialization_alias="grantedScopes")
    missing_scopes: list[str] = Field(serialization_alias="missingScopes")
    can_write_products: bool = Field(serialization_alias="canWriteProducts")
    can_write_content: bool = Field(default=False, serialization_alias="canWriteContent")
    requires_reconnect: bool = Field(serialization_alias="requiresReconnect")
    message: str


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
    cancelled_orders_count: int = Field(default=0, serialization_alias="cancelledOrdersCount")
    unpaid_orders_count: int = Field(default=0, serialization_alias="unpaidOrdersCount")
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


class ShopifyMetricComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current: Decimal
    previous: Decimal
    delta: Decimal
    delta_percent: float | None = Field(default=None, serialization_alias="deltaPercent")
    direction: str


class ShopifySourceComparisonItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str
    revenue: Decimal | None = None
    orders_count: int | None = Field(default=None, serialization_alias="ordersCount")
    previous: Decimal
    delta: Decimal
    delta_percent: float | None = Field(default=None, serialization_alias="deltaPercent")
    direction: str


class ShopifyProductComparisonItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    current_revenue: Decimal = Field(serialization_alias="currentRevenue")
    previous_revenue: Decimal = Field(serialization_alias="previousRevenue")
    current_quantity: int = Field(serialization_alias="currentQuantity")
    previous_quantity: int = Field(serialization_alias="previousQuantity")
    delta: Decimal
    delta_percent: float | None = Field(default=None, serialization_alias="deltaPercent")
    direction: str


class ShopifyProductPeriodItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_title: str = Field(serialization_alias="productTitle")
    quantity_sold: int = Field(serialization_alias="quantitySold")
    revenue: Decimal


class ShopifyComparisonMetrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue: ShopifyMetricComparison
    orders: ShopifyMetricComparison
    average_order_value: ShopifyMetricComparison = Field(
        serialization_alias="averageOrderValue",
    )
    paid_orders: ShopifyMetricComparison = Field(serialization_alias="paidOrders")
    pending_orders: ShopifyMetricComparison = Field(serialization_alias="pendingOrders")
    unfulfilled_orders: ShopifyMetricComparison = Field(
        serialization_alias="unfulfilledOrders",
    )


class ShopifyAttributionComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    revenue_by_source_delta: list[ShopifySourceComparisonItem] = Field(
        serialization_alias="revenueBySourceDelta",
    )
    orders_by_source_delta: list[ShopifySourceComparisonItem] = Field(
        serialization_alias="ordersBySourceDelta",
    )
    top_growing_sources: list[ShopifySourceComparisonItem] = Field(
        serialization_alias="topGrowingSources",
    )
    top_declining_sources: list[ShopifySourceComparisonItem] = Field(
        serialization_alias="topDecliningSources",
    )
    unknown_revenue_delta: ShopifyMetricComparison = Field(
        serialization_alias="unknownRevenueDelta",
    )
    tracking_quality_delta: ShopifyMetricComparison = Field(
        serialization_alias="trackingQualityDelta",
    )


class ShopifyProductComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    top_growing_products: list[ShopifyProductComparisonItem] = Field(
        serialization_alias="topGrowingProducts",
    )
    top_declining_products: list[ShopifyProductComparisonItem] = Field(
        serialization_alias="topDecliningProducts",
    )
    products_new_in_current_period: list[ShopifyProductPeriodItem] = Field(
        serialization_alias="productsNewInCurrentPeriod",
    )
    products_sold_previously_but_not_now: list[ShopifyProductPeriodItem] = Field(
        serialization_alias="productsSoldPreviouslyButNotNow",
    )


class ShopifyDashboardComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current_period: ShopifyDashboardPeriod = Field(serialization_alias="currentPeriod")
    previous_period: ShopifyDashboardPeriod = Field(serialization_alias="previousPeriod")
    data_quality: str = Field(serialization_alias="dataQuality")
    metrics: ShopifyComparisonMetrics
    attribution: ShopifyAttributionComparison
    products: ShopifyProductComparison


class ShopifyReconciliationOrders(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    paid: int
    pending: int
    cancelled: int
    unpaid: int


class ShopifySalesBreakdown(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    gross_sales: Decimal = Field(serialization_alias="grossSales")
    discounts: Decimal
    sales_reversals: Decimal = Field(serialization_alias="salesReversals")
    returns: Decimal
    shipping: Decimal
    taxes: Decimal
    duties: Decimal
    fees: Decimal
    total_sales: Decimal = Field(serialization_alias="totalSales")
    current_total_sum: Decimal = Field(serialization_alias="currentTotalSum")


class ShopifyReconciliationDataQuality(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    warnings: list[str] = Field(default_factory=list)


class ShopifyDashboardReconciliation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metric_mode: str = Field(serialization_alias="metricMode")
    period: ShopifyDashboardPeriod
    orders: ShopifyReconciliationOrders
    sales_breakdown: ShopifySalesBreakdown = Field(serialization_alias="salesBreakdown")
    data_quality: ShopifyReconciliationDataQuality = Field(serialization_alias="dataQuality")


class ShopifyReconciliationRefundItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refund_created_at: datetime | None = Field(
        default=None,
        serialization_alias="refundCreatedAt",
    )
    amount: Decimal
    currency: str | None = None
    order_name: str | None = Field(default=None, serialization_alias="orderName")


class ShopifyReconciliationSampleOrder(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_name: str | None = Field(default=None, serialization_alias="orderName")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    processed_at: datetime | None = Field(default=None, serialization_alias="processedAt")
    financial_status: str | None = Field(default=None, serialization_alias="financialStatus")
    total_price: Decimal = Field(serialization_alias="totalPrice")
    current_total_price: Decimal = Field(serialization_alias="currentTotalPrice")
    refund_total: Decimal | None = Field(default=None, serialization_alias="refundTotal")


class ShopifyReconciliationDebugResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    period: ShopifyDashboardPeriod
    last_sync_at: datetime | None = Field(default=None, serialization_alias="lastSyncAt")
    metric_mode: str = Field(serialization_alias="metricMode")
    order_count_by_financial_status: dict[str, int] = Field(
        serialization_alias="orderCountByFinancialStatus",
    )
    order_count_by_fulfillment_status: dict[str, int] = Field(
        serialization_alias="orderCountByFulfillmentStatus",
    )
    reconciliation: ShopifyDashboardReconciliation
    sales_breakdown: ShopifySalesBreakdown = Field(serialization_alias="salesBreakdown")
    refunds_in_period: list[ShopifyReconciliationRefundItem] = Field(
        serialization_alias="refundsInPeriod",
    )
    sample_orders: list[ShopifyReconciliationSampleOrder] = Field(
        serialization_alias="sampleOrders",
    )


class ShopifyOfficialAnalyticsKpis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_sales: Decimal | None = Field(default=None, serialization_alias="totalSales")
    orders: int | None = None
    average_order_value: Decimal | None = Field(
        default=None,
        serialization_alias="averageOrderValue",
    )
    sessions: int | None = None
    conversion_rate: float | None = Field(default=None, serialization_alias="conversionRate")


class ShopifyOfficialTimeseriesPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str
    total_sales: Decimal | None = Field(default=None, serialization_alias="totalSales")
    orders: int | None = None
    sessions: int | None = None
    conversion_rate: float | None = Field(default=None, serialization_alias="conversionRate")


class ShopifyOfficialChannelRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    channel: str
    total_sales: Decimal = Field(serialization_alias="totalSales")
    orders: int


class ShopifyOfficialUtmRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    source: str
    medium: str
    total_sales: Decimal = Field(serialization_alias="totalSales")
    orders: int


class ShopifyOfficialAnalyticsDataQuality(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    warnings: list[str] = Field(default_factory=list)


class ShopifyOfficialAnalytics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    available: bool
    source: str = "shopifyql"
    kpis: ShopifyOfficialAnalyticsKpis
    timeseries: list[ShopifyOfficialTimeseriesPoint] = Field(default_factory=list)
    sales_by_referring_channel: list[ShopifyOfficialChannelRow] = Field(
        default_factory=list,
        serialization_alias="salesByReferringChannel",
    )
    sales_by_utm_campaign: list[ShopifyOfficialUtmRow] = Field(
        default_factory=list,
        serialization_alias="salesByUtmCampaign",
    )
    data_quality: ShopifyOfficialAnalyticsDataQuality = Field(
        serialization_alias="dataQuality",
    )


class ShopifyAnalyticsReconciliation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    official_total_sales: Decimal | None = Field(
        default=None,
        serialization_alias="officialTotalSales",
    )
    local_total_sales: Decimal = Field(serialization_alias="localTotalSales")
    delta: Decimal | None = None
    delta_percent: float | None = Field(default=None, serialization_alias="deltaPercent")
    message: str


class ShopifyShopifyqlProbeSample(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    columns: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[Any] = Field(default_factory=list)


class ShopifyShopifyqlProbeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    available: bool
    requires_reconnect: bool = Field(serialization_alias="requiresReconnect")
    error_code: str | None = Field(default=None, serialization_alias="errorCode")
    message: str
    sample: ShopifyShopifyqlProbeSample | None = None


class ShopifyOfficialAnalyticsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    period: ShopifyDashboardPeriod
    official_analytics: ShopifyOfficialAnalytics = Field(
        serialization_alias="officialAnalytics",
    )


class ShopifyDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    period: ShopifyDashboardPeriod
    comparison: ShopifyDashboardComparison
    reconciliation: ShopifyDashboardReconciliation
    official_analytics: ShopifyOfficialAnalytics = Field(
        serialization_alias="officialAnalytics",
    )
    analytics_reconciliation: ShopifyAnalyticsReconciliation = Field(
        serialization_alias="analyticsReconciliation",
    )
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
