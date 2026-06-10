import type {
  ComparisonDirection,
  ShopifyDashboardComparison,
  ShopifyMetricComparison,
} from "@gcr/shared";

export function isLimitedComparison(comparison: ShopifyDashboardComparison): boolean {
  return comparison.dataQuality === "limited";
}

export function directionClass(direction: ComparisonDirection): string {
  if (direction === "up") return "shopify-metric-delta--up";
  if (direction === "down") return "shopify-metric-delta--down";
  return "shopify-metric-delta--flat";
}

export function formatDeltaPercent(metric: ShopifyMetricComparison): string {
  if (metric.deltaPercent == null) {
    if (metric.direction === "up") return "nuovo";
    return "—";
  }
  const sign = metric.deltaPercent > 0 ? "+" : "";
  return `${sign}${metric.deltaPercent.toFixed(1)}%`;
}

export function formatDeltaArrow(direction: ComparisonDirection): string {
  if (direction === "up") return "↑";
  if (direction === "down") return "↓";
  return "→";
}

export function getProductTrendBadge(
  productTitle: string,
  comparison: ShopifyDashboardComparison,
): string | null {
  const growing = comparison.products.topGrowingProducts.some(
    (item) => item.productTitle === productTitle,
  );
  const declining = comparison.products.topDecliningProducts.some(
    (item) => item.productTitle === productTitle,
  );
  const isNew = comparison.products.productsNewInCurrentPeriod.some(
    (item) => item.productTitle === productTitle,
  );
  const stalled = comparison.products.productsSoldPreviouslyButNotNow.some(
    (item) => item.productTitle === productTitle,
  );

  if (isNew) return "Nuovo nel periodo";
  if (growing) return "In crescita";
  if (declining) return "In calo";
  if (stalled) return "Fermo vs periodo precedente";
  return null;
}

export function getProductTrendBadgeClass(label: string | null): string {
  if (!label) return "";
  if (label === "In crescita") return "shopify-product-badge--growing";
  if (label === "In calo") return "shopify-product-badge--declining";
  if (label === "Nuovo nel periodo") return "shopify-product-badge--new";
  return "shopify-product-badge--stalled";
}
