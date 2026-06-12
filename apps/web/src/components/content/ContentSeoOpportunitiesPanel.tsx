import { useState } from "react";
import type { ContentOpportunity } from "@gcr/shared";
import { ShowMoreToggle } from "../shopify/ShowMoreToggle";
import { CONTENT_SEO_ROW_LIMIT, sliceContentRows } from "../../lib/content-seo-blocks";

interface ContentSeoOpportunitiesPanelProps {
  opportunities: ContentOpportunity[];
}

export function ContentSeoOpportunitiesPanel({ opportunities }: ContentSeoOpportunitiesPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const visible = sliceContentRows(opportunities, expanded);

  return (
    <section className="gcr-card content-seo-panel">
      <h3 className="shopify-panel__title">Content Opportunities</h3>
      <p className="shopify-panel__context">Idee editoriali e miglioramenti da dati reali dello store</p>

      {opportunities.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna opportunità. Sincronizza e analizza i contenuti.</p>
      ) : (
        <>
          <ul className="shopify-seo-list">
            {visible.map((opp) => (
              <li key={opp.id} className="shopify-seo-list__item content-seo-list__item--stacked">
                <div>
                  <span className="shopify-seo-list__product">{opp.title}</span>
                  <p className="content-seo-list__description">{opp.description}</p>
                </div>
                <span className={`content-seo-badge content-seo-badge--${opp.priority}`}>
                  {opp.priority}
                </span>
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
