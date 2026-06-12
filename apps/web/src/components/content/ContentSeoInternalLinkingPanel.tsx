import { useState } from "react";
import type { ContentOpportunity } from "@gcr/shared";
import { ShowMoreToggle } from "../shopify/ShowMoreToggle";
import { CONTENT_SEO_ROW_LIMIT, sliceContentRows } from "../../lib/content-seo-blocks";

interface ContentSeoInternalLinkingPanelProps {
  opportunities: ContentOpportunity[];
}

export function ContentSeoInternalLinkingPanel({
  opportunities,
}: ContentSeoInternalLinkingPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const visible = sliceContentRows(opportunities, expanded);

  return (
    <section className="gcr-card content-seo-panel">
      <h3 className="shopify-panel__title">Internal Linking Opportunities</h3>
      <p className="shopify-panel__context">Articoli da arricchire con link prodotti e collections</p>

      {opportunities.length === 0 ? (
        <p className="shopify-empty-copy">Nessun suggerimento internal linking.</p>
      ) : (
        <>
          <ul className="shopify-seo-list">
            {visible.map((opp) => (
              <li key={opp.id} className="shopify-seo-list__item content-seo-list__item--stacked">
                <div>
                  <span className="shopify-seo-list__product">{opp.title}</span>
                  <p className="content-seo-list__description">{opp.reason}</p>
                </div>
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
