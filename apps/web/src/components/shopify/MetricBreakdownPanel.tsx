import { useState } from "react";
import type { ShopifyDashboardReconciliation } from "@gcr/shared";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface MetricBreakdownPanelProps {
  reconciliation: ShopifyDashboardReconciliation;
  formatMoney: (value: string) => string;
}

interface BreakdownRow {
  label: string;
  value: string;
  tone?: "positive" | "negative" | "neutral" | "emphasis";
}

export function MetricBreakdownPanel({
  reconciliation,
  formatMoney,
}: MetricBreakdownPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const { salesBreakdown, dataQuality, orders } = reconciliation;

  const rows: BreakdownRow[] = [
    { label: "Gross sales", value: formatMoney(salesBreakdown.grossSales), tone: "neutral" },
    { label: "Discounts", value: `−${formatMoney(salesBreakdown.discounts)}`, tone: "negative" },
    {
      label: "Sales reversals / refunds",
      value: `−${formatMoney(salesBreakdown.salesReversals)}`,
      tone: "negative",
    },
    { label: "Shipping", value: formatMoney(salesBreakdown.shipping), tone: "positive" },
    { label: "Taxes", value: formatMoney(salesBreakdown.taxes), tone: "positive" },
    {
      label: "Total sales (Shopify-like)",
      value: formatMoney(salesBreakdown.totalSales),
      tone: "emphasis",
    },
    {
      label: "Current order total sum",
      value: formatMoney(salesBreakdown.currentTotalSum),
      tone: "neutral",
    },
  ];

  const visibleRows = expanded ? rows : rows.slice(0, 4);

  return (
    <section className="shopify-metric-breakdown gcr-card">
      <div className="shopify-metric-breakdown__header">
        <div>
          <h2 className="shopify-panel__title">Metric Breakdown</h2>
          <p className="shopify-panel__context">
            {orders.total} ordini piazzati nel periodo · {orders.paid} pagati · {orders.pending}{" "}
            pending
          </p>
        </div>
        <ShowMoreToggle
          total={rows.length}
          limit={4}
          expanded={expanded}
          onToggle={() => setExpanded((value) => !value)}
        />
      </div>

      {dataQuality.status !== "ok" && dataQuality.warnings.length > 0 && (
        <div className={`shopify-metric-breakdown__banner shopify-metric-breakdown__banner--${dataQuality.status}`}>
          {dataQuality.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}

      <div className="shopify-metric-breakdown__grid">
        {visibleRows.map((row) => (
          <div
            key={row.label}
            className={`shopify-metric-breakdown__row shopify-metric-breakdown__row--${row.tone ?? "neutral"}`}
          >
            <span className="shopify-metric-breakdown__label">{row.label}</span>
            <span className="shopify-metric-breakdown__value">{row.value}</span>
          </div>
        ))}
      </div>

      <p className="shopify-metric-breakdown__footnote">
        Questa metrica prova ad allinearsi alla logica Shopify Analytics. Per parità perfetta
        useremo ShopifyQL/read_reports nello step successivo.
      </p>
    </section>
  );
}
