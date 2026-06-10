import { useState } from "react";
import type { ShopifyDashboardProduct, ShopifySeoSection } from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT, sliceWithLimit } from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface SeoOpportunitiesPanelProps {
  seoOpportunities: ShopifySeoSection;
}

function ProductList({
  products,
  issueLabel,
}: {
  products: ShopifyDashboardProduct[];
  issueLabel: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleProducts = sliceWithLimit(products, SHOPIFY_TABLE_ROW_LIMIT, expanded);

  if (products.length === 0) return null;

  return (
    <div className="shopify-seo-section">
      <h4 className="shopify-panel__subtitle">{issueLabel}</h4>
      <ul className="shopify-seo-list">
        {visibleProducts.map((product) => (
          <li key={`${issueLabel}-${product.title}`} className="shopify-seo-list__item">
            <span className="shopify-seo-list__product">{product.title}</span>
            <span className="shopify-seo-list__issue">{issueLabel}</span>
          </li>
        ))}
      </ul>
      <ShowMoreToggle
        total={products.length}
        limit={SHOPIFY_TABLE_ROW_LIMIT}
        expanded={expanded}
        onToggle={() => setExpanded((value) => !value)}
      />
    </div>
  );
}

export function SeoOpportunitiesPanel({ seoOpportunities }: SeoOpportunitiesPanelProps) {
  const totalIssues =
    seoOpportunities.productsMissingMetaTitle.length +
    seoOpportunities.productsMissingMetaDescription.length +
    seoOpportunities.productsMissingBoth.length;

  return (
    <section className="shopify-seo-panel gcr-card">
      <h3 className="shopify-panel__title">SEO Opportunities</h3>
      <p className="shopify-panel__context">Stato attuale dello store</p>

      <div className="shopify-seo-stats">
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">
            {seoOpportunities.productsMissingMetaTitle.length}
          </span>
          <span className="shopify-seo-stats__label">Meta title mancante</span>
        </div>
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">
            {seoOpportunities.productsMissingMetaDescription.length}
          </span>
          <span className="shopify-seo-stats__label">Meta description mancante</span>
        </div>
        <div className="shopify-seo-stats__item">
          <span className="shopify-seo-stats__value">
            {seoOpportunities.productsMissingBoth.length}
          </span>
          <span className="shopify-seo-stats__label">Entrambi mancanti</span>
        </div>
      </div>

      <ProductList
        products={seoOpportunities.productsMissingMetaTitle}
        issueLabel="Meta title mancante"
      />
      <ProductList
        products={seoOpportunities.productsMissingMetaDescription}
        issueLabel="Meta description mancante"
      />
      <ProductList
        products={seoOpportunities.productsMissingBoth}
        issueLabel="Meta title e description mancanti"
      />

      {seoOpportunities.seoOpportunities.length > 0 && (
        <div className="shopify-seo-section">
          <h4 className="shopify-panel__subtitle">Candidati SEO da prodotti senza vendite</h4>
          <ul className="shopify-seo-list">
            {seoOpportunities.seoOpportunities.slice(0, SHOPIFY_TABLE_ROW_LIMIT).map((opp) => (
              <li key={`${opp.productTitle}-${opp.issue}`} className="shopify-seo-list__item">
                <span className="shopify-seo-list__product">{opp.productTitle}</span>
                <span className="shopify-seo-list__issue">{opp.issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {totalIssues === 0 && seoOpportunities.seoOpportunities.length === 0 && (
        <p className="shopify-empty-copy">Nessun problema SEO rilevato sui prodotti attivi.</p>
      )}

      <button type="button" className="gcr-btn gcr-btn--secondary shopify-seo-cta" disabled>
        Genera piano contenuti — Coming soon
      </button>
    </section>
  );
}
