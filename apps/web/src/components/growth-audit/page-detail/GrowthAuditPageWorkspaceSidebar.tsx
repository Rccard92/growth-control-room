import type { GrowthAuditPage } from "@gcr/shared";
import {
  buildGrowthAuditPageWorkflowSteps,
  getGrowthAuditPageAiMetadata,
  getGrowthAuditPageAnalyticsMetadata,
  getGrowthAuditPagePerformanceMetadata,
  getGrowthAuditPageSearchConsoleMetadata,
  getGrowthAuditSourceEntityTypeLabel,
  getGrowthAuditWorkflowStepStatusLabel,
  getGrowthAuditWorkspaceOperativeNote,
  isGrowthAuditPageShopifyLinked,
  mapGrowthAuditPageToSeoEntity,
  type GrowthAuditWorkflowStepStatus,
} from "../../../lib/growth-audit-utils";

export interface GrowthAuditPageWorkspaceSidebarProps {
  page: GrowthAuditPage;
  priorityActionsCount: number;
  openFindingsCount: number;
  openTasksCount: number;
  hasAiResult: boolean;
  hasPerformanceResult?: boolean;
  hasSearchConsoleData?: boolean;
  hasAnalyticsData?: boolean;
  shopifySectionAvailable: boolean;
  aiSectionAvailable: boolean;
  onScrollToSection: (sectionId: string) => void;
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("it-IT");
  } catch {
    return value;
  }
}

function getWorkflowStepClass(status: GrowthAuditWorkflowStepStatus): string {
  if (status === "done") return "growth-audit-workflow-step growth-audit-workflow-step--done";
  if (status === "recommended") {
    return "growth-audit-workflow-step growth-audit-workflow-step--active";
  }
  if (status === "available") {
    return "growth-audit-workflow-step growth-audit-workflow-step--available";
  }
  return "growth-audit-workflow-step";
}

export function GrowthAuditPageWorkspaceSidebar({
  page,
  priorityActionsCount,
  openFindingsCount,
  openTasksCount,
  hasAiResult,
  hasPerformanceResult = false,
  hasSearchConsoleData = false,
  hasAnalyticsData = false,
  shopifySectionAvailable,
  aiSectionAvailable,
  onScrollToSection,
}: GrowthAuditPageWorkspaceSidebarProps) {
  const aiMeta = getGrowthAuditPageAiMetadata(page);
  const performanceMeta = getGrowthAuditPagePerformanceMetadata(page);
  const searchConsoleMeta = getGrowthAuditPageSearchConsoleMetadata(page);
  const analyticsMeta = getGrowthAuditPageAnalyticsMetadata(page);
  const shopifyLinked = isGrowthAuditPageShopifyLinked(page);
  const mappedEntity = mapGrowthAuditPageToSeoEntity(page);

  const workflowSteps = buildGrowthAuditPageWorkflowSteps({
    page,
    priorityActionsCount,
    hasAiResult,
    hasPerformanceResult,
    hasSearchConsoleData,
    hasAnalyticsData,
    shopifyEditable: shopifySectionAvailable && Boolean(mappedEntity),
    openFindingsCount,
  });

  return (
    <aside className="growth-audit-workspace-sidebar growth-audit-workspace__sidebar">
      <section className="growth-audit-workflow-card gcr-card">
        <h3 className="growth-audit-workspace-sidebar__title">Workflow consigliato</h3>
        <ol className="growth-audit-workflow-card__steps">
          {workflowSteps.map((step, index) => (
            <li key={step.key} className={getWorkflowStepClass(step.status)}>
              <span className="growth-audit-workflow-step__index">{index + 1}</span>
              <div className="growth-audit-workflow-step__content">
                <span className="growth-audit-workflow-step__label">{step.label}</span>
                <span className="growth-audit-workflow-step__status">
                  {getGrowthAuditWorkflowStepStatusLabel(step.status)}
                </span>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="growth-audit-workspace-sidebar__block gcr-card">
        <h3 className="growth-audit-workspace-sidebar__title">Stato pagina</h3>
        <dl className="growth-audit-workspace-sidebar__meta">
          <div>
            <dt>Ultima scansione tecnica</dt>
            <dd>{formatDate(page.analyzedAt)}</dd>
          </div>
          <div>
            <dt>Ultima analisi AI</dt>
            <dd>{formatDate(aiMeta?.analyzedAt)}</dd>
          </div>
          <div>
            <dt>Ultima analisi performance</dt>
            <dd>{formatDate(performanceMeta?.analyzedAt)}</dd>
          </div>
          <div>
            <dt>Ultima sync Search Console</dt>
            <dd>{formatDate(searchConsoleMeta?.syncedAt)}</dd>
          </div>
          <div>
            <dt>Ultima sync GA4</dt>
            <dd>{formatDate(analyticsMeta?.syncedAt)}</dd>
          </div>
          <div>
            <dt>Problemi aperti</dt>
            <dd>{openFindingsCount}</dd>
          </div>
          <div>
            <dt>Task aperti</dt>
            <dd>{openTasksCount}</dd>
          </div>
          {shopifyLinked && page.sourceEntityTitle && (
            <div>
              <dt>Entità Shopify</dt>
              <dd>{page.sourceEntityTitle}</dd>
            </div>
          )}
          {shopifyLinked && page.sourceEntityHandle && (
            <div>
              <dt>Handle</dt>
              <dd>{page.sourceEntityHandle}</dd>
            </div>
          )}
          {shopifyLinked && page.sourceEntityType && (
            <div>
              <dt>Tipo entità</dt>
              <dd>{getGrowthAuditSourceEntityTypeLabel(page.sourceEntityType)}</dd>
            </div>
          )}
        </dl>
      </section>

      <section className="growth-audit-workspace-sidebar__block gcr-card">
        <h3 className="growth-audit-workspace-sidebar__title">Collegamenti rapidi</h3>
        <div className="growth-audit-workspace-sidebar__links">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("priority-actions")}
          >
            Cosa sistemare prima
          </button>
          {shopifySectionAvailable && mappedEntity && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("shopify-edit")}
            >
              Modifica Shopify
            </button>
          )}
          {aiSectionAvailable && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("ai-geo-cro")}
            >
              AI/GEO/CRO
            </button>
          )}
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("performance")}
          >
            Performance
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("search-console")}
          >
            Search Console
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("analytics")}
          >
            GA4
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("technical-data")}
          >
            Dati tecnici
          </button>
        </div>
      </section>

      <section className="growth-audit-workspace-sidebar__block gcr-card">
        <h3 className="growth-audit-workspace-sidebar__title">Nota operativa</h3>
        <p className="growth-audit-workspace-sidebar__note">
          {getGrowthAuditWorkspaceOperativeNote(page.pageType)}
        </p>
      </section>
    </aside>
  );
}
