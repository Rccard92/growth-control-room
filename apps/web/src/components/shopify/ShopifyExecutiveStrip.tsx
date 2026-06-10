import type { ShopifyDashboardSummary } from "@gcr/shared";

interface ShopifyExecutiveStripProps {
  summary: ShopifyDashboardSummary;
  formatMoney: (value: string) => string;
}

interface KpiItem {
  label: string;
  value: string | number;
  meta?: string;
  accent?: string;
}

export function ShopifyExecutiveStrip({ summary, formatMoney }: ShopifyExecutiveStripProps) {
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
      label: "Scorte basse",
      value: summary.lowStockCount,
      meta: `${summary.outOfStockCount} out of stock`,
      accent: "amber",
    },
    {
      label: "Alert critici",
      value: summary.criticalAlertsCount,
      meta: "Richiedono azione",
      accent: "rose",
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
