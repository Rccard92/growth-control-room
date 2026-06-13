export interface ShopifyOAuthStartResponse {
  authorizationUrl: string;
}

export interface ShopifyConnectRequest {
  shopDomain: string;
  adminAccessToken: string;
}

export interface ShopifyConnectResponse {
  connected: boolean;
  shopDomain: string;
  shopName?: string | null;
  connectionStatus: string;
}

export interface ShopifyStatus {
  connected: boolean;
  shopDomain?: string | null;
  shopName?: string | null;
  lastSyncAt?: string | null;
}

export interface ShopifyScopesResponse {
  shopDomain: string;
  configuredScopes: string[];
  grantedScopes: string[];
  missingScopes: string[];
  canWriteProducts: boolean;
  requiresReconnect: boolean;
  message: string;
}

export interface ShopifySyncResponse {
  productsSynced: number;
  variantsSynced?: number;
  ordersSynced: number;
  lineItemsSynced?: number;
  metricsSynced: number;
  durationSeconds?: number;
  lastSyncAt: string;
}

export interface ShopifyTopProduct {
  productGid: string;
  title: string;
  quantitySold: number;
}

export interface ShopifyProductSummary {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  status?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
}

export interface ShopifyOrderSummary {
  id: string;
  shopifyGid: string;
  orderName?: string | null;
  createdAtShopify?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  currency?: string | null;
  customerEmail?: string | null;
}

export interface ShopifyDashboardPeriod {
  range: string;
  startDate: string;
  endDate: string;
  timezone: string;
  label: string;
}

export type ComparisonDirection = "up" | "down" | "flat";

export interface ShopifyMetricComparison {
  current: string | number;
  previous: string | number;
  delta: string | number;
  deltaPercent: number | null;
  direction: ComparisonDirection;
}

export interface ShopifySourceComparisonItem {
  source: string;
  revenue?: string;
  ordersCount?: number;
  previous: string | number;
  delta: string | number;
  deltaPercent: number | null;
  direction: ComparisonDirection;
}

export interface ShopifyProductComparisonItem {
  productTitle: string;
  currentRevenue: string;
  previousRevenue: string;
  currentQuantity: number;
  previousQuantity: number;
  delta: string | number;
  deltaPercent: number | null;
  direction: ComparisonDirection;
}

export interface ShopifyProductPeriodItem {
  productTitle: string;
  quantitySold: number;
  revenue: string;
}

export interface ShopifyComparisonMetrics {
  revenue: ShopifyMetricComparison;
  orders: ShopifyMetricComparison;
  averageOrderValue: ShopifyMetricComparison;
  paidOrders: ShopifyMetricComparison;
  pendingOrders: ShopifyMetricComparison;
  unfulfilledOrders: ShopifyMetricComparison;
}

export interface ShopifyAttributionComparison {
  revenueBySourceDelta: ShopifySourceComparisonItem[];
  ordersBySourceDelta: ShopifySourceComparisonItem[];
  topGrowingSources: ShopifySourceComparisonItem[];
  topDecliningSources: ShopifySourceComparisonItem[];
  unknownRevenueDelta: ShopifyMetricComparison;
  trackingQualityDelta: ShopifyMetricComparison;
}

export interface ShopifyProductComparison {
  topGrowingProducts: ShopifyProductComparisonItem[];
  topDecliningProducts: ShopifyProductComparisonItem[];
  productsNewInCurrentPeriod: ShopifyProductPeriodItem[];
  productsSoldPreviouslyButNotNow: ShopifyProductPeriodItem[];
}

export interface ShopifyDashboardComparison {
  currentPeriod: ShopifyDashboardPeriod;
  previousPeriod: ShopifyDashboardPeriod;
  dataQuality: "full" | "limited";
  metrics: ShopifyComparisonMetrics;
  attribution: ShopifyAttributionComparison;
  products: ShopifyProductComparison;
}

export interface ShopifyReconciliationOrders {
  total: number;
  paid: number;
  pending: number;
  cancelled: number;
  unpaid: number;
}

export interface ShopifySalesBreakdown {
  grossSales: string;
  discounts: string;
  salesReversals: string;
  returns: string;
  shipping: string;
  taxes: string;
  duties: string;
  fees: string;
  totalSales: string;
  currentTotalSum: string;
}

export type ShopifyReconciliationDataQualityStatus = "ok" | "limited" | "warning";

export interface ShopifyReconciliationDataQuality {
  status: ShopifyReconciliationDataQualityStatus;
  warnings: string[];
}

export interface ShopifyDashboardReconciliation {
  metricMode: string;
  period: ShopifyDashboardPeriod;
  orders: ShopifyReconciliationOrders;
  salesBreakdown: ShopifySalesBreakdown;
  dataQuality: ShopifyReconciliationDataQuality;
}

export interface ShopifyOfficialAnalyticsKpis {
  totalSales: string | null;
  orders: number | null;
  averageOrderValue: string | null;
  sessions: number | null;
  conversionRate: number | null;
}

export interface ShopifyOfficialTimeseriesPoint {
  date: string;
  totalSales: string | null;
  orders: number | null;
  sessions?: number | null;
  conversionRate?: number | null;
}

export interface ShopifyOfficialChannelRow {
  channel: string;
  totalSales: string;
  orders: number;
}

export interface ShopifyOfficialUtmRow {
  name: string;
  source: string;
  medium: string;
  totalSales: string;
  orders: number;
}

export type ShopifyOfficialAnalyticsDataQualityStatus = "ok" | "limited" | "unavailable";

export interface ShopifyOfficialAnalyticsDataQuality {
  status: ShopifyOfficialAnalyticsDataQualityStatus;
  warnings: string[];
}

export interface ShopifyOfficialAnalytics {
  available: boolean;
  source: string;
  kpis: ShopifyOfficialAnalyticsKpis;
  timeseries: ShopifyOfficialTimeseriesPoint[];
  salesByReferringChannel: ShopifyOfficialChannelRow[];
  salesByUtmCampaign: ShopifyOfficialUtmRow[];
  dataQuality: ShopifyOfficialAnalyticsDataQuality;
}

export interface ShopifyAnalyticsReconciliation {
  officialTotalSales: string | null;
  localTotalSales: string;
  delta: string | null;
  deltaPercent: number | null;
  message: string;
}

export interface ShopifyShopifyqlProbeResponse {
  available: boolean;
  requiresReconnect: boolean;
  errorCode: string | null;
  message: string;
  sample?: {
    columns: Record<string, unknown>[];
    rows: unknown[];
  } | null;
}

export interface ShopifyPeriodMetrics {
  revenue: string;
  ordersCount: number;
  averageOrderValue: string;
  paidOrdersCount: number;
  pendingOrdersCount: number;
  cancelledOrdersCount?: number;
  unpaidOrdersCount?: number;
  fulfilledOrdersCount: number;
  unfulfilledOrdersCount: number;
  productsWithoutSalesCount: number;
}

export interface ShopifyCurrentStateMetrics {
  productsCount: number;
  activeProductsCount: number;
  draftProductsCount: number;
  lowStockCount: number;
  outOfStockCount: number;
  seoIssuesCount: number;
}

export interface ShopifyDashboardSummary {
  revenue: string;
  ordersCount: number;
  averageOrderValue: string;
  productsCount: number;
  activeProductsCount: number;
  draftProductsCount: number;
  paidOrdersCount: number;
  pendingOrdersCount: number;
  fulfilledOrdersCount: number;
  unfulfilledOrdersCount: number;
  lowStockCount: number;
  outOfStockCount: number;
  productsWithoutSalesCount: number;
  seoIssuesCount: number;
  criticalAlertsCount: number;
  lastSyncAt?: string | null;
  shopDomain: string;
  periodMetrics: ShopifyPeriodMetrics;
  currentStateMetrics: ShopifyCurrentStateMetrics;
}

export interface ShopifyDashboardProduct {
  title: string;
  status?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
  productType?: string | null;
  vendor?: string | null;
  handle?: string | null;
}

export interface ShopifyDashboardOrder {
  orderName?: string | null;
  createdAtShopify?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  currency?: string | null;
}

export interface ShopifyDashboardAlert {
  id: string;
  severity: ShopifyInsightSeverity;
  title: string;
  description: string;
  entityType: "product" | "order" | "inventory" | "seo" | "attribution" | "sync";
  entityId?: string | null;
  actionLabel?: string | null;
}

export interface ShopifyBestSellerPerformance {
  productTitle: string;
  sku?: string | null;
  quantitySold: number;
  revenue: string;
  currentInventory?: number | null;
  status?: string | null;
}

export interface ShopifyNoSalesProduct {
  productTitle: string;
  currentInventory?: number | null;
  status?: string | null;
  productType?: string | null;
  seoIssue: boolean;
}

export interface ShopifyHighStockLowSales {
  productTitle: string;
  currentInventory?: number | null;
  quantitySold: number;
  issue: string;
}

export interface ShopifyProductPerformanceSection {
  bestSellers: ShopifyBestSellerPerformance[];
  noSalesProducts: ShopifyNoSalesProduct[];
  highStockLowSales: ShopifyHighStockLowSales[];
}

export type ShopifyProductIntelligenceSection = ShopifyProductPerformanceSection;
export type ShopifyInventoryRiskSection = ShopifyInventorySection;
export type ShopifyOrderOperationsSection = ShopifyOrdersSection;
export type ShopifySeoOpportunitiesSection = ShopifySeoSection;

export interface ShopifyInventorySummary {
  totalUnits: number;
  activeProducts: number;
  zeroStockActiveProducts: number;
  lowStockActiveProducts: number;
}

export interface ShopifyInventorySection {
  lowStockProducts: ShopifyDashboardProduct[];
  outOfStockProducts: ShopifyDashboardProduct[];
  inventorySummary: ShopifyInventorySummary;
}

export interface ShopifyOrdersSection {
  recentOrders: ShopifyDashboardOrder[];
  pendingOrders: ShopifyDashboardOrder[];
  unfulfilledOrders: ShopifyDashboardOrder[];
}

export interface ShopifySeoOpportunity {
  productTitle: string;
  issue: string;
  priority: string;
}

export interface ShopifySeoSection {
  productsMissingMetaTitle: ShopifyDashboardProduct[];
  productsMissingMetaDescription: ShopifyDashboardProduct[];
  productsMissingBoth: ShopifyDashboardProduct[];
  seoOpportunities: ShopifySeoOpportunity[];
}

export interface ShopifyAttributionReadiness {
  connectedSources: string[];
  channelBreakdown: Record<string, unknown>[];
  utmCoverage: number | null;
  message: string;
}

export interface ShopifyAttributionBreakdownItem {
  source?: string | null;
  channel?: string | null;
  campaign?: string | null;
  revenue: string;
  ordersCount: number;
}

export interface ShopifyNewReturningBySource {
  source: string;
  newCount: number;
  returningCount: number;
  unknownCount: number;
  revenue: string;
}

export interface ShopifyTopProductBySource {
  source: string;
  productTitle: string;
  revenue: string;
  ordersCount: number;
}

export interface ShopifyAttributionIntelligence {
  revenueBySource: ShopifyAttributionBreakdownItem[];
  ordersBySource: ShopifyAttributionBreakdownItem[];
  revenueByChannel: ShopifyAttributionBreakdownItem[];
  ordersByChannel: ShopifyAttributionBreakdownItem[];
  revenueByUtmCampaign: ShopifyAttributionBreakdownItem[];
  ordersByUtmCampaign: ShopifyAttributionBreakdownItem[];
  newVsReturningBySource: ShopifyNewReturningBySource[];
  topProductsBySource: ShopifyTopProductBySource[];
  unattributedOrdersCount: number;
  unattributedRevenue: string;
  directOrdersCount: number;
  unknownOrdersCount: number;
  trackingQualityScore: number;
}

export interface ShopifyMarketingReportAvailability {
  shopifyOrderAttributionAvailable: boolean;
  shopifyqlAvailable: boolean | null;
  message: string;
}

export type ShopifyInsightSeverity = "info" | "warning" | "critical" | "opportunity";

export interface ShopifyDailyDiagnosisItem {
  message: string;
  severity: ShopifyInsightSeverity;
}

export interface ShopifyDashboard {
  period: ShopifyDashboardPeriod;
  comparison: ShopifyDashboardComparison;
  reconciliation: ShopifyDashboardReconciliation;
  officialAnalytics: ShopifyOfficialAnalytics;
  analyticsReconciliation: ShopifyAnalyticsReconciliation;
  summary: ShopifyDashboardSummary;
  alerts: ShopifyDashboardAlert[];
  productIntelligence?: ShopifyProductPerformanceSection;
  attributionIntelligence: ShopifyAttributionIntelligence;
  inventoryRisk?: ShopifyInventorySection;
  orderOperations?: ShopifyOrdersSection;
  seoOpportunities?: ShopifySeoSection;
  dailyDiagnosis: ShopifyDailyDiagnosisItem[];
  // Backward compatibility
  productPerformance: ShopifyProductPerformanceSection;
  inventory: ShopifyInventorySection;
  orders: ShopifyOrdersSection;
  seo: ShopifySeoSection;
  attribution: ShopifyAttributionReadiness;
  marketingReportAvailability: ShopifyMarketingReportAvailability;
}

export interface ShopifyProduct {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  status?: string | null;
  vendor?: string | null;
  productType?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
  seoTitle?: string | null;
  seoDescription?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ShopifyOrder {
  id: string;
  shopifyGid: string;
  orderName?: string | null;
  createdAtShopify?: string | null;
  processedAt?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  subtotalPrice?: string | null;
  currency?: string | null;
  customerEmail?: string | null;
  createdAt: string;
  updatedAt: string;
}
