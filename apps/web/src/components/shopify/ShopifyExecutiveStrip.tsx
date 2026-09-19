import type {
  ShopifyDashboardComparison,
  ShopifyDashboardReconciliation,
  ShopifyDashboardSummary,
  ShopifyMetricComparison,
  ShopifyOfficialAnalytics,
  ShopifyOrderDataCoverage,
} from "@gcr/shared";
import {
  directionClass,
  formatDeltaArrow,
  formatDeltaPercent,
} from "../../lib/shopify-comparison-format";

interface ShopifyExecutiveStripProps {
  summary: ShopifyDashboardSummary;
  reconciliation: ShopifyDashboardReconciliation;
  officialAnalytics: ShopifyOfficialAnalytics;
  trackingQualityScore: number;
  formatMoney: (value: string) => string;
  periodLabel?: string;
  comparison?: ShopifyDashboardComparison;
  orderDataCoverage?: ShopifyOrderDataCoverage;
}

interface KpiItem {
  label: string;
  value: string | number;
  meta?: string;
  accent?: string;
  comparisonMetric?: ShopifyMetricComparison;
}

function MetricDelta({ metric }: { metric: ShopifyMetricComparison }) {
  return (
    <span className={`shopify-metric-delta ${directionClass(metric.direction)}`}>
      {formatDeltaArrow(metric.direction)} {formatDeltaPercent(metric)}{" "}
      <span className="shopify-metric-delta__hint">vs periodo precedente</span>
    </span>
  );
}

export function ShopifyExecutiveStrip({
  summary,
  reconciliation,
  officialAnalytics,
  trackingQualityScore,
  formatMoney,
  periodLabel,
  comparison,
  orderDataCoverage,
}: ShopifyExecutiveStripProps) {
  // With no order data for the period, every order KPI computes to zero. Showing
  // "0,00 EUR" would read as "no sales" instead of "we do not know".
  const ordersUnavailable = orderDataCoverage?.orderMetricsReliable === false;
  const unavailable = "n/d";
  const scoreClass =
    trackingQualityScore >= 70 ? "emerald" : trackingQualityScore >= 40 ? "amber" : "rose";
  const metrics = comparison?.metrics;
  const trackingDelta = comparison?.attribution.trackingQualityDelta;
  const { salesBreakdown, orders } = reconciliation;
  const useOfficial =
    officialAnalytics.available &&
    officialAnalytics.kpis.totalSales != null &&
    officialAnalytics.kpis.orders != null;

  const revenueValue = useOfficial
    ? formatMoney(officialAnalytics.kpis.totalSales!)
    : formatMoney(salesBreakdown.totalSales);
  const ordersValue = useOfficial ? officialAnalytics.kpis.orders! : orders.total;
  const aovValue =
    useOfficial && officialAnalytics.kpis.averageOrderValue != null
      ? formatMoney(officialAnalytics.kpis.averageOrderValue)
      : formatMoney(summary.averageOrderValue);

  const items: KpiItem[] = [
    {
      label: "Revenue",
      value: ordersUnavailable ? unavailable : revenueValue,
      meta: ordersUnavailable
        ? "Dati non sincronizzati"
        : useOfficial
          ? "Total sales ShopifyQL"
          : "Total sales Shopify-like",
      accent: ordersUnavailable ? "default" : "violet",
      comparisonMetric: ordersUnavailable ? undefined : metrics?.revenue,
    },
    {
      label: "Ordini",
      value: ordersUnavailable ? unavailable : ordersValue,
      meta: ordersUnavailable
        ? "Dati non sincronizzati"
        : `${orders.paid} pagati · ${orders.pending} pending`,
      accent: ordersUnavailable ? "default" : "cyan",
      comparisonMetric: ordersUnavailable ? undefined : metrics?.orders,
    },
    {
      label: "AOV",
      value: ordersUnavailable ? unavailable : aovValue,
      meta: ordersUnavailable ? "Dati non sincronizzati" : undefined,
      accent: "default",
      comparisonMetric: ordersUnavailable ? undefined : metrics?.averageOrderValue,
    },
    {
      label: "Prodotti attivi",
      value: summary.activeProductsCount,
      meta: `${summary.productsCount} totali`,
      accent: "emerald",
    },
    {
      label: "Alert critici",
      value: summary.criticalAlertsCount,
      meta: "Richiedono azione",
      accent: "rose",
    },
    {
      label: "Tracking quality score",
      value: ordersUnavailable ? unavailable : `${trackingQualityScore}%`,
      meta: ordersUnavailable ? "Dati non sincronizzati" : "Attribution Shopify",
      accent: ordersUnavailable ? "default" : scoreClass,
      comparisonMetric: ordersUnavailable ? undefined : trackingDelta,
    },
  ];

  return (
    <div className="shopify-executive-strip-wrap">
      {periodLabel && (
        <p className="shopify-panel__context">Performance del periodo: {periodLabel}</p>
      )}
      {orderDataCoverage?.message && (
        <div
          className={`shopify-coverage-banner shopify-coverage-banner--${
            ordersUnavailable ? "critical" : "warning"
          }`}
          role="status"
        >
          {orderDataCoverage.message}
        </div>
      )}
      <div className="shopify-executive-strip">
        {items.map((item) => (
          <div
            key={item.label}
            className={`shopify-kpi shopify-kpi--${item.accent ?? "default"}`}
          >
            <p className="shopify-kpi__label">{item.label}</p>
            <p className="shopify-kpi__value">{item.value}</p>
            {item.comparisonMetric && <MetricDelta metric={item.comparisonMetric} />}
            {item.meta && <p className="shopify-kpi__meta">{item.meta}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
