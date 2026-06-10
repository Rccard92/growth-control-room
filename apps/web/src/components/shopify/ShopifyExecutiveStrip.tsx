import type { ShopifyDashboardSummary } from "@gcr/shared";

interface ShopifyExecutiveStripProps {
  summary: ShopifyDashboardSummary;
  trackingQualityScore: number;
  formatMoney: (value: string) => string;
}

interface KpiItem {
  label: string;
  value: string | number;
  meta?: string;
  accent?: string;
}

export function ShopifyExecutiveStrip({
  summary,
  trackingQualityScore,
  formatMoney,
}: ShopifyExecutiveStripProps) {
  const scoreClass =
    trackingQualityScore >= 70 ? "emerald" : trackingQualityScore >= 40 ? "amber" : "rose";

  const items: KpiItem[] = [
    {
      label: "Revenue",
      value: formatMoney(summary.revenue),
      meta: `${summary.paidOrdersCount} pagati`,
      accent: "violet",
    },
    {
      label: "Ordini",
      value: summary.ordersCount,
      meta: `${summary.pendingOrdersCount} pending`,
      accent: "cyan",
    },
    {
      label: "AOV",
      value: formatMoney(summary.averageOrderValue),
      accent: "default",
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
    },
  ];

  return (
    <div className="shopify-executive-strip">
      {items.map((item) => (
        <div
          key={item.label}
          className={`shopify-kpi shopify-kpi--${item.accent ?? "default"}`}
        >
          <p className="shopify-kpi__label">{item.label}</p>
          <p className="shopify-kpi__value">{item.value}</p>
          {item.meta && <p className="shopify-kpi__meta">{item.meta}</p>}
        </div>
      ))}
    </div>
  );
}
