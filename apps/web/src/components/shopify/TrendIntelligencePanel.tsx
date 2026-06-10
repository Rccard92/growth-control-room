import type { ShopifyDashboardComparison } from "@gcr/shared";
import {
  directionClass,
  formatDeltaArrow,
  formatDeltaPercent,
  isLimitedComparison,
} from "../../lib/shopify-comparison-format";
import { formatShopifyMoney } from "../../lib/shopify-format";

interface TrendIntelligencePanelProps {
  comparison: ShopifyDashboardComparison;
}

interface TrendRow {
  label: string;
  current: string;
  deltaLabel: string;
  direction: "up" | "down" | "flat";
}

export function TrendIntelligencePanel({ comparison }: TrendIntelligencePanelProps) {
  const { metrics, attribution, products } = comparison;

  const rows: TrendRow[] = [
    {
      label: "Revenue trend",
      current: formatShopifyMoney(String(metrics.revenue.current), "EUR"),
      deltaLabel: formatDeltaPercent(metrics.revenue),
      direction: metrics.revenue.direction,
    },
    {
      label: "Orders trend",
      current: String(metrics.orders.current),
      deltaLabel: formatDeltaPercent(metrics.orders),
      direction: metrics.orders.direction,
    },
    {
      label: "AOV trend",
      current: formatShopifyMoney(String(metrics.averageOrderValue.current), "EUR"),
      deltaLabel: formatDeltaPercent(metrics.averageOrderValue),
      direction: metrics.averageOrderValue.direction,
    },
    {
      label: "Tracking quality trend",
      current: `${attribution.trackingQualityDelta.current}%`,
      deltaLabel: formatDeltaPercent(attribution.trackingQualityDelta),
      direction: attribution.trackingQualityDelta.direction,
    },
  ];

  const topGrowingSource = attribution.topGrowingSources[0];
  if (topGrowingSource) {
    rows.push({
      label: "Top growing source",
      current: topGrowingSource.source,
      deltaLabel: formatDeltaPercent({
        current: topGrowingSource.revenue ?? 0,
        previous: topGrowingSource.previous,
        delta: topGrowingSource.delta,
        deltaPercent: topGrowingSource.deltaPercent,
        direction: topGrowingSource.direction,
      }),
      direction: topGrowingSource.direction,
    });
  }

  const topDecliningSource = attribution.topDecliningSources[0];
  if (topDecliningSource) {
    rows.push({
      label: "Top declining source",
      current: topDecliningSource.source,
      deltaLabel: formatDeltaPercent({
        current: topDecliningSource.revenue ?? 0,
        previous: topDecliningSource.previous,
        delta: topDecliningSource.delta,
        deltaPercent: topDecliningSource.deltaPercent,
        direction: topDecliningSource.direction,
      }),
      direction: topDecliningSource.direction,
    });
  }

  const topGrowingProduct = products.topGrowingProducts[0];
  if (topGrowingProduct) {
    rows.push({
      label: "Top growing product",
      current: topGrowingProduct.productTitle,
      deltaLabel: formatDeltaPercent({
        current: topGrowingProduct.currentRevenue,
        previous: topGrowingProduct.previousRevenue,
        delta: topGrowingProduct.delta,
        deltaPercent: topGrowingProduct.deltaPercent,
        direction: topGrowingProduct.direction,
      }),
      direction: topGrowingProduct.direction,
    });
  }

  const topDecliningProduct = products.topDecliningProducts[0];
  if (topDecliningProduct) {
    rows.push({
      label: "Top declining product",
      current: topDecliningProduct.productTitle,
      deltaLabel: formatDeltaPercent({
        current: topDecliningProduct.currentRevenue,
        previous: topDecliningProduct.previousRevenue,
        delta: topDecliningProduct.delta,
        deltaPercent: topDecliningProduct.deltaPercent,
        direction: topDecliningProduct.direction,
      }),
      direction: topDecliningProduct.direction,
    });
  }

  return (
    <section className="shopify-trend-intel gcr-card">
      <h3 className="shopify-panel__title">Trend Intelligence</h3>
      <p className="shopify-panel__context">Confronto vs periodo precedente equivalente</p>

      {isLimitedComparison(comparison) && (
        <p className="shopify-trend-intel__limited">
          Confronto limitato: non ci sono abbastanza dati nel periodo precedente.
        </p>
      )}

      <div className="shopify-trend-intel__grid">
        {rows.slice(0, 8).map((row) => (
          <div key={row.label} className="shopify-trend-intel__item">
            <span className="shopify-trend-intel__label">{row.label}</span>
            <span className="shopify-trend-intel__value">{row.current}</span>
            <span className={`shopify-metric-delta ${directionClass(row.direction)}`}>
              {formatDeltaArrow(row.direction)} {row.deltaLabel}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
