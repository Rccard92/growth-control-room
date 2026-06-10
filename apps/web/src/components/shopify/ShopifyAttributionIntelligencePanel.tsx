import type {
  ShopifyAttributionIntelligence,
  ShopifyMarketingReportAvailability,
} from "@gcr/shared";

interface ShopifyAttributionIntelligencePanelProps {
  intelligence: ShopifyAttributionIntelligence;
  availability: ShopifyMarketingReportAvailability;
  formatMoney: (value: string, currency?: string | null) => string;
}

function sourceChipClass(source: string): string {
  const normalized = source.toLowerCase();
  if (normalized.includes("email") || normalized.includes("klaviyo")) return "shopify-source-chip--email";
  if (normalized.includes("social") || normalized.includes("facebook") || normalized.includes("instagram") || normalized.includes("meta")) {
    return "shopify-source-chip--social";
  }
  if (normalized.includes("google") || normalized.includes("search")) return "shopify-source-chip--search";
  if (normalized === "direct") return "shopify-source-chip--direct";
  return "";
}

export function ShopifyAttributionIntelligencePanel({
  intelligence,
  availability,
  formatMoney,
}: ShopifyAttributionIntelligencePanelProps) {
  const hasData = availability.shopifyOrderAttributionAvailable;
  const score = intelligence.trackingQualityScore;
  const scoreClass =
    score >= 70 ? "shopify-quality-score--good" : score >= 40 ? "shopify-quality-score--mid" : "shopify-quality-score--low";

  return (
    <section className="shopify-attribution-intel gcr-card">
      <h3 className="shopify-panel__title">Shopify Attribution Intelligence</h3>
      <p className="shopify-panel__subtitle">{availability.message}</p>

      {!hasData ? (
        <p className="shopify-empty-copy">
          Attribution non disponibile dai dati ordine Shopify. Esegui un re-sync dopo il deploy
          per popolare source, channel e UTM dagli ordini.
        </p>
      ) : (
        <>
          <div className={`shopify-quality-score ${scoreClass}`}>
            <span className="shopify-quality-score__value">{score}%</span>
            <span className="shopify-quality-score__label">Tracking quality score</span>
          </div>

          <div className="shopify-attribution-metrics">
            <div className="shopify-attribution-metrics__item">
              <span className="shopify-attribution-metrics__value">
                {formatMoney(intelligence.unattributedRevenue)}
              </span>
              <span className="shopify-attribution-metrics__label">
                Unknown revenue ({intelligence.unattributedOrdersCount} ordini)
              </span>
            </div>
            <div className="shopify-attribution-metrics__item">
              <span className="shopify-attribution-metrics__value">
                {intelligence.directOrdersCount}
              </span>
              <span className="shopify-attribution-metrics__label">Ordini Direct</span>
            </div>
          </div>

          <h4 className="shopify-panel__subtitle">Revenue by source</h4>
          {intelligence.revenueBySource.length === 0 ? (
            <p className="shopify-empty-copy">Non disponibile dai dati ordine Shopify.</p>
          ) : (
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Revenue</th>
                  <th>Ordini</th>
                </tr>
              </thead>
              <tbody>
                {intelligence.revenueBySource.slice(0, 8).map((row) => (
                  <tr key={row.source ?? "unknown"}>
                    <td>
                      <span className={`shopify-source-chip ${sourceChipClass(row.source ?? "")}`}>
                        {row.source ?? "Unknown"}
                      </span>
                    </td>
                    <td>{formatMoney(row.revenue)}</td>
                    <td>{row.ordersCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4 className="shopify-panel__subtitle">Orders by source</h4>
          {intelligence.ordersBySource.length === 0 ? (
            <p className="shopify-empty-copy">Non disponibile dai dati ordine Shopify.</p>
          ) : (
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Ordini</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {intelligence.ordersBySource.slice(0, 8).map((row) => (
                  <tr key={`orders-${row.source}`}>
                    <td>{row.source ?? "Unknown"}</td>
                    <td>{row.ordersCount}</td>
                    <td>{formatMoney(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4 className="shopify-panel__subtitle">Top UTM campaigns</h4>
          {intelligence.revenueByUtmCampaign.length === 0 ? (
            <p className="shopify-empty-copy">
              UTM campaign non disponibile dai dati ordine Shopify (customer journey assente o
              senza UTM).
            </p>
          ) : (
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Revenue</th>
                  <th>Ordini</th>
                </tr>
              </thead>
              <tbody>
                {intelligence.revenueByUtmCampaign.slice(0, 8).map((row) => (
                  <tr key={row.campaign ?? "none"}>
                    <td>{row.campaign ?? "—"}</td>
                    <td>{formatMoney(row.revenue)}</td>
                    <td>{row.ordersCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4 className="shopify-panel__subtitle">New vs returning by source</h4>
          {intelligence.newVsReturningBySource.length === 0 ? (
            <p className="shopify-empty-copy">Non disponibile dai dati ordine Shopify.</p>
          ) : (
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>New</th>
                  <th>Returning</th>
                  <th>Unknown</th>
                </tr>
              </thead>
              <tbody>
                {intelligence.newVsReturningBySource.slice(0, 8).map((row) => (
                  <tr key={`nr-${row.source}`}>
                    <td>{row.source}</td>
                    <td>{row.newCount}</td>
                    <td>{row.returningCount}</td>
                    <td>{row.unknownCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4 className="shopify-panel__subtitle">Top products by source</h4>
          {intelligence.topProductsBySource.length === 0 ? (
            <p className="shopify-empty-copy">Non disponibile dai dati ordine Shopify.</p>
          ) : (
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Prodotto</th>
                  <th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {intelligence.topProductsBySource.slice(0, 8).map((row) => (
                  <tr key={`${row.source}-${row.productTitle}`}>
                    <td>{row.source}</td>
                    <td>{row.productTitle}</td>
                    <td>{formatMoney(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
