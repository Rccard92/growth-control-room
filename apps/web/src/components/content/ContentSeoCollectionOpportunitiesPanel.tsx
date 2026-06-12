import { useState } from "react";
import type { ContentOpportunity } from "@gcr/shared";
import { ShowMoreToggle } from "../shopify/ShowMoreToggle";
import { CONTENT_SEO_ROW_LIMIT, sliceContentRows } from "../../lib/content-seo-blocks";

interface ContentSeoCollectionOpportunitiesPanelProps {
  opportunities: ContentOpportunity[];
}

export function ContentSeoCollectionOpportunitiesPanel({
  opportunities,
}: ContentSeoCollectionOpportunitiesPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const visible = sliceContentRows(opportunities, expanded);

  return (
    <section className="gcr-card content-seo-panel">
      <h3 className="shopify-panel__title">Collection SEO Opportunities</h3>
      <p className="shopify-panel__context">Pillar content e SEO collection</p>

      {opportunities.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna opportunità collection al momento.</p>
      ) : (
        <>
          <ul className="shopify-seo-list">
            {visible.map((opp) => (
              <li key={opp.id} className="shopify-seo-list__item">
                <span className="shopify-seo-list__product">{opp.title}</span>
                <span className="shopify-seo-list__issue">{opp.opportunityType}</span>
              </li>
            ))}
          </ul>
          <ShowMoreToggle
            total={opportunities.length}
            limit={CONTENT_SEO_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}
    </section>
  );
}
