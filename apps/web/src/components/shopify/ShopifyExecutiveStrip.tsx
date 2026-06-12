import type {
  ShopifyDashboardComparison,
  ShopifyDashboardReconciliation,
  ShopifyDashboardSummary,
  ShopifyMetricComparison,
} from "@gcr/shared";
import {
  directionClass,
  formatDeltaArrow,
  formatDeltaPercent,
} from "../../lib/shopify-comparison-format";

interface ShopifyExecutiveStripProps {
  summary: ShopifyDashboardSummary;
  reconciliation: ShopifyDashboardReconciliation;
  trackingQualityScore: number;
  formatMoney: (value: string) => string;
  periodLabel?: string;
  comparison?: ShopifyDashboardComparison;
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
  trackingQualityScore,
  formatMoney,
  periodLabel,
  comparison,
}: ShopifyExecutiveStripProps) {
  const scoreClass =
    trackingQualityScore >= 70 ? "emerald" : trackingQualityScore >= 40 ? "amber" : "rose";
  const metrics = comparison?.metrics;
  const trackingDelta = comparison?.attribution.trackingQualityDelta;
  const { salesBreakdown, orders } = reconciliation;

  const items: KpiItem[] = [
    {
      label: "Revenue",
      value: formatMoney(salesBreakdown.totalSales),
      meta: "Total sales Shopify-like",
      accent: "violet",
      comparisonMetric: metrics?.revenue,
    },
    {
      label: "Ordini",
      value: orders.total,
      meta: `${orders.paid} pagati · ${orders.pending} pending`,
      accent: "cyan",
      comparisonMetric: metrics?.orders,
    },
    {
      label: "AOV",
      value: formatMoney(summary.averageOrderValue),
      accent: "default",
      comparisonMetric: metrics?.averageOrderValue,
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
      value: `${trackingQualityScore}%`,
      meta: "Attribution Shopify",
      accent: scoreClass,
      comparisonMetric: trackingDelta,
    },
  ];

  return (
    <div className="shopify-executive-strip-wrap">
      {periodLabel && (
        <p className="shopify-panel__context">Performance del periodo: {periodLabel}</p>
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
