import type { GrowthAuditFinding, GrowthAuditPage } from "@gcr/shared";
import {
  buildGrowthAuditPageImprovementItems,
  getGrowthAuditImprovementHeadline,
  getGrowthAuditImprovementStatusLabel,
  getGrowthAuditImprovementSummaryText,
  type GrowthAuditImprovementStatus,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageImprovementPanelProps {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
}

function statusBadgeClass(status: GrowthAuditImprovementStatus): string {
  return `growth-audit-improvement-badge growth-audit-improvement-badge--${status}`;
}

export function GrowthAuditPageImprovementPanel({
  page,
  findings,
}: GrowthAuditPageImprovementPanelProps) {
  const headline = getGrowthAuditImprovementHeadline(page);
  const summary = getGrowthAuditImprovementSummaryText(page);
  const items = buildGrowthAuditPageImprovementItems(page, findings);

  return (
    <section className="growth-audit-page-drawer__section growth-audit-improvement-panel">
      <h4 className="growth-audit-page-drawer__section-title">Come migliorare questa pagina</h4>
      <p className="growth-audit-improvement-panel__headline">{headline.text}</p>
      <p className="growth-audit-improvement-panel__summary">{summary}</p>
      <ul className="growth-audit-improvement-panel__list">
        {items.map((item) => (
          <li key={item.key} className="growth-audit-improvement-panel__item">
            <div className="growth-audit-improvement-panel__item-header">
              <span className={statusBadgeClass(item.status)}>
                {getGrowthAuditImprovementStatusLabel(item.status)}
              </span>
              <strong>{item.label}</strong>
            </div>
            <p className="growth-audit-improvement-panel__item-title">{item.title}</p>
            <p className="growth-audit-improvement-panel__item-description">{item.description}</p>
            {item.evidence && (
              <p className="growth-audit-improvement-panel__item-evidence">
                Evidenza: {item.evidence}
              </p>
            )}
            <div className="growth-audit-improvement-panel__recommendation">
              <span className="growth-audit-improvement-panel__recommendation-label">
                Come risolvere
              </span>
              <p>{item.recommendation}</p>
            </div>
            <p className="growth-audit-improvement-panel__validate">
              <span className="growth-audit-improvement-panel__validate-label">
                Come verificare
              </span>{" "}
              {item.howToValidate}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
