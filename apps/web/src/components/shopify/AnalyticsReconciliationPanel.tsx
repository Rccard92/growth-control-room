import type { ShopifyAnalyticsReconciliation } from "@gcr/shared";
import { formatDeltaPercent } from "../../lib/shopify-comparison-format";

interface AnalyticsReconciliationPanelProps {
  analyticsReconciliation: ShopifyAnalyticsReconciliation;
  formatMoney: (value: string) => string;
}

export function AnalyticsReconciliationPanel({
  analyticsReconciliation,
  formatMoney,
}: AnalyticsReconciliationPanelProps) {
  const {
    officialTotalSales,
    localTotalSales,
    delta,
    deltaPercent,
    message,
  } = analyticsReconciliation;

  const deltaDirection =
    delta == null ? "flat" : Number(delta) > 0 ? "up" : Number(delta) < 0 ? "down" : "flat";

  return (
    <section className="shopify-analytics-recon gcr-card">
      <h2 className="shopify-panel__title">Analytics Reconciliation</h2>
      <p className="shopify-panel__context">
        Confronto tra total sales ufficiali ShopifyQL e calcolo locale
      </p>

      <div className="shopify-analytics-recon__grid">
        <div className="shopify-analytics-recon__item">
          <span className="shopify-analytics-recon__label">ShopifyQL total sales</span>
          <span className="shopify-analytics-recon__value">
            {officialTotalSales != null ? formatMoney(officialTotalSales) : "—"}
          </span>
        </div>
        <div className="shopify-analytics-recon__item">
          <span className="shopify-analytics-recon__label">Local total sales</span>
          <span className="shopify-analytics-recon__value">
            {formatMoney(localTotalSales)}
          </span>
        </div>
        <div className="shopify-analytics-recon__item">
          <span className="shopify-analytics-recon__label">Differenza</span>
          <span className={`shopify-analytics-recon__value shopify-metric-delta shopify-metric-delta--${deltaDirection}`}>
            {delta != null ? formatMoney(delta) : "—"}
            {deltaPercent != null && (
              <span className="shopify-analytics-recon__percent">
                {" "}
                ({formatDeltaPercent({
                  current: officialTotalSales ?? 0,
                  previous: localTotalSales,
                  delta: delta ?? 0,
                  deltaPercent,
                  direction: deltaDirection,
                })})
              </span>
            )}
          </span>
        </div>
      </div>

      <p className="shopify-analytics-recon__message">{message}</p>
    </section>
  );
}
