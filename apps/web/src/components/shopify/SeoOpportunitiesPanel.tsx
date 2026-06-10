import type { ShopifySeoSection } from "@gcr/shared";

interface SeoOpportunitiesPanelProps {
  seo: ShopifySeoSection;
}

export function SeoOpportunitiesPanel({ seo }: SeoOpportunitiesPanelProps) {
  const totalIssues =
    seo.productsMissingMetaTitle.length +
    seo.productsMissingMetaDescription.length +
    seo.productsMissingBoth.length;

  return (
    <section className="shopify-seo-panel gcr-card">
      <h3 className="shopify-panel__title">SEO Opportunities</h3>

      <div className="shopify-seo-stats">
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">{seo.productsMissingMetaTitle.length}</span>
          <span className="shopify-seo-stats__label">Meta title mancante</span>
        </div>
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">
            {seo.productsMissingMetaDescription.length}
          </span>
          <span className="shopify-seo-stats__label">Meta description mancante</span>
        </div>
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">{seo.productsMissingBoth.length}</span>
          <span className="shopify-seo-stats__label">Entrambi mancanti</span>
        </div>
      </div>

      {seo.seoOpportunities.length > 0 && (
        <ul className="shopify-seo-list">
          {seo.seoOpportunities.slice(0, 6).map((opp) => (
            <li key={`${opp.productTitle}-${opp.issue}`} className="shopify-seo-list__item">
              <span className="shopify-seo-list__product">{opp.productTitle}</span>
              <span className="shopify-seo-list__issue">{opp.issue}</span>
            </li>
          ))}
        </ul>
      )}

      {totalIssues === 0 && (
        <p className="shopify-empty-copy">Nessun problema SEO rilevato sui prodotti attivi.</p>
      )}

      <button type="button" className="gcr-btn gcr-btn--secondary shopify-seo-cta" disabled>
        Genera piano contenuti
      </button>
      <p className="shopify-seo-cta__hint">CTA disponibile in una prossima release.</p>
    </section>
  );
}
