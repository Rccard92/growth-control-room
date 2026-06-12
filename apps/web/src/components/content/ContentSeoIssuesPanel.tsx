import { useState } from "react";
import type { SeoAuditIssue } from "@gcr/shared";
import { ShowMoreToggle } from "../shopify/ShowMoreToggle";
import { CONTENT_SEO_ROW_LIMIT, sliceContentRows } from "../../lib/content-seo-blocks";

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Critico",
  warning: "Warning",
  opportunity: "Opportunità",
  info: "Info",
};

interface ContentSeoIssuesPanelProps {
  issues: SeoAuditIssue[];
}

export function ContentSeoIssuesPanel({ issues }: ContentSeoIssuesPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const visible = sliceContentRows(issues, expanded);

  return (
    <section className="gcr-card content-seo-panel">
      <h3 className="shopify-panel__title">SEO Audit Issues</h3>
      <p className="shopify-panel__context">Problemi rilevati su prodotti, collections, pagine e articoli</p>

      {issues.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna issue aperta. Esegui Analizza SEO dopo il sync.</p>
      ) : (
        <>
          <ul className="shopify-seo-list">
            {visible.map((issue) => (
              <li key={issue.id} className="shopify-seo-list__item content-seo-list__item--stacked">
                <div>
                  <span className="shopify-seo-list__product">{issue.title}</span>
                  <p className="content-seo-list__description">{issue.description}</p>
                </div>
                <span className={`content-seo-badge content-seo-badge--${issue.severity}`}>
                  {SEVERITY_LABEL[issue.severity] ?? issue.severity}
                </span>
              </li>
            ))}
          </ul>
          <ShowMoreToggle
            total={issues.length}
            limit={CONTENT_SEO_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}
    </section>
  );
}
