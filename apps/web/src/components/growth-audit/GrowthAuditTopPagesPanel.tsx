import { Link } from "react-router-dom";
import {
  formatGrowthAuditScore,
  getGrowthAuditPriorityLevelBadgeClass,
  getGrowthAuditPriorityLevelLabel,
  getGrowthAuditScoreBadgeClass,
  type GrowthAuditPagePriorityItem,
} from "../../lib/growth-audit-utils";
import { APP_ROUTES } from "../../routes/config";

interface GrowthAuditTopPagesPanelProps {
  projectId: string;
  runId: string;
  items: GrowthAuditPagePriorityItem[];
  maxItems?: number;
}

export function GrowthAuditTopPagesPanel({
  projectId,
  runId,
  items,
  maxItems = 6,
}: GrowthAuditTopPagesPanelProps) {
  const topItems = items.slice(0, maxItems);

  if (topItems.length === 0) {
    return (
      <section className="growth-audit-top-pages">
        <h3 className="growth-audit-top-pages__title">Top pagine da correggere</h3>
        <p className="growth-audit-top-pages__empty">
          Nessuna pagina prioritaria al momento. L&apos;inventario è in buono stato.
        </p>
      </section>
    );
  }

  return (
    <section className="growth-audit-top-pages">
      <h3 className="growth-audit-top-pages__title">Top pagine da correggere</h3>
      <ul className="growth-audit-top-pages__list">
        {topItems.map((item) => (
          <li key={item.pageId} className={getGrowthAuditPriorityLevelBadgeClass(item.priorityLevel)}>
            <div className="growth-audit-top-page-card__header">
              <span className="growth-audit-top-page-card__badge">
                {getGrowthAuditPriorityLevelLabel(item.priorityLevel)}
              </span>
              <span className="growth-audit-top-page-card__type">{item.pageTypeLabel}</span>
              {item.isShopifyLinked && (
                <span className="growth-audit-top-page-card__shopify">Shopify collegata</span>
              )}
            </div>

            <h4 className="growth-audit-top-page-card__title">{item.title}</h4>
            <p className="growth-audit-top-page-card__url">{item.url}</p>

            <div className="growth-audit-top-page-card__score">
              <div>
                <span className="growth-audit-top-page-card__score-label">Score tecnico</span>
                <span className={getGrowthAuditScoreBadgeClass(item.score)}>
                  {formatGrowthAuditScore(item.score)}
                </span>
              </div>
              {item.aiScore != null && (
                <div>
                  <span className="growth-audit-top-page-card__score-label">AI</span>
                  <span className={getGrowthAuditScoreBadgeClass(item.aiScore)}>
                    {formatGrowthAuditScore(item.aiScore)}
                  </span>
                </div>
              )}
              {item.geoScore != null && (
                <div>
                  <span className="growth-audit-top-page-card__score-label">GEO</span>
                  <span>{item.geoScore}</span>
                </div>
              )}
              {item.croScore != null && (
                <div>
                  <span className="growth-audit-top-page-card__score-label">CRO</span>
                  <span>{item.croScore}</span>
                </div>
              )}
            </div>

            <p className="growth-audit-top-page-card__issues">
              {item.openFindings} problemi aperti
              {item.highPriorityFindings > 0 && ` · ${item.highPriorityFindings} alta priorità`}
              {item.openTasks > 0 && ` · ${item.openTasks} task`}
            </p>

            {item.reasons.length > 0 && (
              <ul className="growth-audit-top-page-card__reasons">
                {item.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}

            <p className="growth-audit-top-page-card__action-hint">{item.recommendedNextAction}</p>

            <Link
              to={APP_ROUTES.projectGrowthAuditPageDetail(projectId, runId, item.pageId)}
              className="growth-audit-top-page-card__cta gcr-btn gcr-btn--primary gcr-btn--sm"
            >
              Gestisci pagina
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
