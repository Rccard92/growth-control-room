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

export interface ShopifySyncResponse {
  productsSynced: number;
  ordersSynced: number;
  metricsSynced: number;
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
  summary: ShopifyDashboardSummary;
  alerts: ShopifyDashboardAlert[];
  productPerformance: ShopifyProductPerformanceSection;
  inventory: ShopifyInventorySection;
  orders: ShopifyOrdersSection;
  seo: ShopifySeoSection;
  attribution: ShopifyAttributionReadiness;
  attributionIntelligence: ShopifyAttributionIntelligence;
  marketingReportAvailability: ShopifyMarketingReportAvailability;
  dailyDiagnosis: ShopifyDailyDiagnosisItem[];
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
