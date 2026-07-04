import type { GrowthAuditPage } from "@gcr/shared";
import type { GrowthAuditFinding, GrowthAuditTask } from "@gcr/shared";
import {
  buildGrowthAuditPagePriorityActions,
  getGrowthAuditFindingSeverityLabel,
  getGrowthAuditOwnerTypeLabel,
  getGrowthAuditSeverityBadgeClass,
  getGrowthAuditTaskPriorityLabel,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPagePriorityActionsProps {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
}

export function GrowthAuditPagePriorityActions({
  page,
  findings,
  tasks,
}: GrowthAuditPagePriorityActionsProps) {
  const actions = buildGrowthAuditPagePriorityActions(page, findings, tasks);

  return (
    <section
      id="section-priority"
      className="growth-audit-page-detail__section growth-audit-page-detail__priority"
    >
      <h2 className="growth-audit-page-detail__section-title">Cosa sistemare prima</h2>
      {actions.length === 0 ? (
        <p className="growth-audit-page-detail__empty">
          Questa pagina non ha criticità prioritarie. Lavora sui miglioramenti di dettaglio per
          aumentare solidità SEO, GEO e CRO.
        </p>
      ) : (
        <ul className="growth-audit-page-detail__priority-list">
          {actions.map((action) => (
            <li key={action.key} className="growth-audit-page-detail__priority-card gcr-card">
              <div className="growth-audit-page-detail__priority-card-header">
                <span className={getGrowthAuditSeverityBadgeClass(action.priority)}>
                  {action.kind === "finding"
                    ? getGrowthAuditFindingSeverityLabel(action.priority)
                    : action.kind === "task"
                      ? getGrowthAuditTaskPriorityLabel(action.priority)
                      : action.priority}
                </span>
                <span className="growth-audit-page-detail__priority-category">
                  {action.category}
                </span>
              </div>
              <h3 className="growth-audit-page-detail__priority-title">{action.title}</h3>
              {action.description && (
                <p className="growth-audit-page-detail__priority-description">
                  <span className="growth-audit-page-detail__field-label">Cosa succede</span>
                  {action.description}
                </p>
              )}
              <div className="growth-audit-page-detail__priority-recommendation">
                <span className="growth-audit-page-detail__field-label">Come risolvere</span>
                <p>{action.recommendation}</p>
              </div>
              {action.howToValidate && (
                <p className="growth-audit-page-detail__priority-validate">
                  <span className="growth-audit-page-detail__field-label">Come verificare</span>
                  {action.howToValidate}
                </p>
              )}
              {(action.ownerType || action.effort) && (
                <div className="growth-audit-page-detail__priority-meta">
                  {action.ownerType && (
                    <span>Owner: {getGrowthAuditOwnerTypeLabel(action.ownerType)}</span>
                  )}
                  {action.effort && <span>Sforzo: {action.effort}</span>}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
