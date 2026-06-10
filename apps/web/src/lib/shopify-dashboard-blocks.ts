import type { ShopifyDashboard } from "@gcr/shared";

export const SHOPIFY_TABLE_ROW_LIMIT = 8;
export const SHOPIFY_DIAGNOSIS_LIMIT = 5;

export interface ResolvedShopifyDashboardBlocks {
  comparison: ShopifyDashboard["comparison"];
  productIntelligence: ShopifyDashboard["productPerformance"];
  inventoryRisk: ShopifyDashboard["inventory"];
  orderOperations: ShopifyDashboard["orders"];
  seoOpportunities: ShopifyDashboard["seo"];
  attributionIntelligence: ShopifyDashboard["attributionIntelligence"];
  marketingReportAvailability: ShopifyDashboard["marketingReportAvailability"];
  alerts: ShopifyDashboard["alerts"];
  dailyDiagnosis: ShopifyDashboard["dailyDiagnosis"];
  summary: ShopifyDashboard["summary"];
}

export function resolveShopifyDashboardBlocks(
  dashboard: ShopifyDashboard,
): ResolvedShopifyDashboardBlocks {
  return {
    comparison: dashboard.comparison,
    productIntelligence: dashboard.productIntelligence ?? dashboard.productPerformance,
    inventoryRisk: dashboard.inventoryRisk ?? dashboard.inventory,
    orderOperations: dashboard.orderOperations ?? dashboard.orders,
    seoOpportunities: dashboard.seoOpportunities ?? dashboard.seo,
    attributionIntelligence: dashboard.attributionIntelligence,
    marketingReportAvailability: dashboard.marketingReportAvailability,
    alerts: dashboard.alerts,
    dailyDiagnosis: dashboard.dailyDiagnosis,
    summary: dashboard.summary,
  };
}

export function sliceWithLimit<T>(items: T[], limit: number, expanded: boolean): T[] {
  if (expanded || items.length <= limit) return items;
  return items.slice(0, limit);
}
