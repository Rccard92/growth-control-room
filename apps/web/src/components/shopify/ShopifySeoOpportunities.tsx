import type { ShopifyDashboardProduct, ShopifySeoOpportunity } from "@gcr/shared";

interface ShopifySeoOpportunitiesProps {
  opportunities: ShopifySeoOpportunity[];
  draftProducts: ShopifyDashboardProduct[];
}

export function ShopifySeoOpportunities({
  opportunities,
  draftProducts,
}: ShopifySeoOpportunitiesProps) {
  const missingTitle = opportunities.filter((item) =>
    item.issue.toLowerCase().includes("meta title"),
  ).length;
  const missingDescription = opportunities.filter((item) =>
    item.issue.toLowerCase().includes("meta description"),
  ).length;

  return (
    <div className="shopify-panel shopify-panel--seo">
      <div className="shopify-panel__header">
        <h3 className="shopify-panel__title">SEO Opportunities</h3>
        <p className="shopify-panel__subtitle">Migliora visibilità e readiness contenuti</p>
      </div>

      <div className="shopify-seo-stats">
        <div className="shopify-seo-stat">
          <span className="shopify-seo-stat__value">{missingTitle}</span>
          <span className="shopify-seo-stat__label">Senza meta title</span>
        </div>
        <div className="shopify-seo-stat">
          <span className="shopify-seo-stat__value">{missingDescription}</span>
          <span className="shopify-seo-stat__label">Senza meta description</span>
        </div>
        <div className="shopify-seo-stat">
          <span className="shopify-seo-stat__value">{draftProducts.length}</span>
          <span className="shopify-seo-stat__label">Prodotti draft</span>
        </div>
      </div>

      {!opportunities.length ? (
        <p className="shopify-empty-copy">Nessuna opportunità SEO critica rilevata.</p>
      ) : (
        <ul className="shopify-seo-list">
          {opportunities.slice(0, 8).map((item) => (
            <li key={`${item.productTitle}-${item.issue}`}>
              <strong>{item.productTitle}</strong>
              <span>{item.issue}</span>
              <span className={`shopify-badge shopify-badge--${item.priority === "high" ? "critical" : "warning"}`}>
                {item.priority}
              </span>
            </li>
          ))}
        </ul>
      )}

      <button type="button" className="gcr-btn gcr-btn--secondary" disabled>
        Genera idee contenuto
      </button>
    </div>
  );
}
