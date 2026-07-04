import { useState } from "react";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditPageResult, GrowthAuditTask } from "@gcr/shared";
import {
  buildGrowthAuditPageImprovementItems,
  buildGrowthAuditPriorityActions,
  getGrowthAuditEffortLabel,
  getGrowthAuditOwnerTypeLabel,
  getGrowthAuditPriorityActionBadgeClass,
  getGrowthAuditPriorityActionCategoryLabel,
  getGrowthAuditPriorityActionLabel,
  getGrowthAuditWhereToFix,
  mapGrowthAuditPageToSeoEntity,
  type GrowthAuditPriorityAction,
} from "../../lib/growth-audit-utils";

export interface GrowthAuditPriorityActionsPanelProps {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  aiResults?: GrowthAuditPageResult[];
  maxItems?: number;
  compact?: boolean;
  sectionId?: string;
  workspace?: boolean;
}

function isCommercePage(page: GrowthAuditPage): boolean {
  return page.pageType === "product" || page.pageType === "landing_page";
}

function getPriorityActionAnchor(
  action: GrowthAuditPriorityAction,
  page: GrowthAuditPage,
): { id: string; label: string } | null {
  const shopifyLinked = Boolean(mapGrowthAuditPageToSeoEntity(page));
  if (
    shopifyLinked &&
    (action.category === "seo" ||
      action.category === "shopify" ||
      action.category === "content" ||
      action.category === "cro" ||
      action.category === "geo" ||
      action.category === "images")
  ) {
    return { id: "shopify-edit", label: "Vai a Modifica Shopify" };
  }
  if (
    action.category === "technical" ||
    action.category === "schema" ||
    action.ownerType === "dev"
  ) {
    return { id: "technical-data", label: "Vai ai dati tecnici" };
  }
  if (shopifyLinked) {
    return { id: "shopify-edit", label: "Vai a Modifica Shopify" };
  }
  return null;
}

export function GrowthAuditPriorityActionsPanel({
  page,
  findings,
  tasks,
  aiResults,
  maxItems,
  compact = false,
  sectionId,
  workspace = false,
}: GrowthAuditPriorityActionsPanelProps) {
  const [showAll, setShowAll] = useState(false);
  const improvementItems = buildGrowthAuditPageImprovementItems(page, findings);
  const allActions = buildGrowthAuditPriorityActions({
    page,
    findings,
    tasks,
    improvementItems,
    aiResults,
  });
  const resolvedSectionId = sectionId ?? (compact ? "section-priority" : "priority-actions");
  const shouldLimit = maxItems != null && !showAll;
  const actions = shouldLimit ? allActions.slice(0, maxItems) : allActions;
  const hasHiddenActions = maxItems != null && allActions.length > maxItems;

  const highPriorityCount = allActions.filter(
    (action) => action.priority === "critical" || action.priority === "high",
  ).length;
  const quickWinCount = allActions.filter((action) => action.effort === "low").length;
  const croAdsCount = allActions.filter(
    (action) => action.category === "cro" || action.category === "ads",
  ).length;

  return (
    <section
      id={resolvedSectionId}
      className={`growth-audit-priority-actions${workspace ? " growth-audit-workspace-section" : " growth-audit-page-detail__section growth-audit-page-detail__priority"}${compact ? " growth-audit-priority-actions--compact" : ""}`}
    >
      <header className="growth-audit-priority-actions__header">
        <h2 className="growth-audit-priority-actions__title">Cosa sistemare prima</h2>
        <p className="growth-audit-priority-actions__subtitle">
          Azioni ordinate per priorità, impatto e facilità di intervento.
        </p>
        {!compact && (
          <>
            <p className="growth-audit-priority-actions__microcopy">
              Questa lista unisce problemi tecnici, suggerimenti AI e azioni aperte. Parti dalle
              azioni in alto.
            </p>
            {isCommercePage(page) && (
              <p className="growth-audit-priority-actions__microcopy growth-audit-priority-actions__microcopy--commerce">
                Su pagine prodotto/landing, CRO e Ads hanno priorità rispetto ai dettagli tecnici
                minori.
              </p>
            )}
          </>
        )}
      </header>

      {actions.length > 0 && (
        <div className="growth-audit-priority-actions__kpis" aria-label="Riepilogo azioni prioritarie">
          <div className="growth-audit-priority-actions__kpi">
            <span className="growth-audit-priority-actions__kpi-value">{allActions.length}</span>
            <span className="growth-audit-priority-actions__kpi-label">Azioni totali</span>
          </div>
          <div className="growth-audit-priority-actions__kpi">
            <span className="growth-audit-priority-actions__kpi-value">{highPriorityCount}</span>
            <span className="growth-audit-priority-actions__kpi-label">Alta priorità</span>
          </div>
          <div className="growth-audit-priority-actions__kpi">
            <span className="growth-audit-priority-actions__kpi-value">{quickWinCount}</span>
            <span className="growth-audit-priority-actions__kpi-label">Quick win</span>
          </div>
          <div className="growth-audit-priority-actions__kpi">
            <span className="growth-audit-priority-actions__kpi-value">{croAdsCount}</span>
            <span className="growth-audit-priority-actions__kpi-label">CRO / Ads</span>
          </div>
        </div>
      )}

      {actions.length === 0 ? (
        <div className="growth-audit-priority-actions__empty">
          <p>
            Nessuna azione prioritaria aperta su questa pagina. Valuta un&apos;analisi AI/GEO/CRO
            sulle pagine strategiche per scoprire opportunità di crescita.
          </p>
        </div>
      ) : (
        <ul className="growth-audit-priority-actions__list">
          {actions.map((action) => {
            const whereToFix = action.whereToFix ?? getGrowthAuditWhereToFix(action, page);
            const anchor = getPriorityActionAnchor(action, page);

            return (
              <li key={action.id} className={getGrowthAuditPriorityActionBadgeClass(action.priority)}>
                <div className="growth-audit-priority-action-card__meta">
                  <span className="growth-audit-priority-action-card__badge">
                    {getGrowthAuditPriorityActionLabel(action.priority)}
                  </span>
                  <span className="growth-audit-priority-action-card__category">
                    {getGrowthAuditPriorityActionCategoryLabel(action.category)}
                  </span>
                  <span className="growth-audit-priority-action-card__owner">
                    Responsabile: {getGrowthAuditOwnerTypeLabel(action.ownerType)}
                  </span>
                  <span className="growth-audit-priority-action-card__effort">
                    Sforzo: {getGrowthAuditEffortLabel(action.effort)}
                  </span>
                </div>

                <h3 className="growth-audit-priority-action-card__title">{action.title}</h3>

                {action.description && (
                  <p className="growth-audit-priority-action-card__description">{action.description}</p>
                )}

                {action.evidence && (
                  <p className="growth-audit-priority-action-card__evidence">
                    <span className="growth-audit-priority-action-card__field-label">Evidenza</span>
                    {action.evidence}
                  </p>
                )}

                {action.whyItMatters && (
                  <p className="growth-audit-priority-action-card__why">
                    <span className="growth-audit-priority-action-card__field-label">Perché conta</span>
                    {action.whyItMatters}
                  </p>
                )}

                <div className="growth-audit-priority-action-card__recommendation">
                  <span className="growth-audit-priority-action-card__field-label">Come risolvere</span>
                  <p>{action.recommendation}</p>
                </div>

                <div className="growth-audit-priority-action-card__where">
                  <span className="growth-audit-priority-action-card__field-label">Dove intervenire</span>
                  <p>{whereToFix}</p>
                </div>

                {action.howToValidate && (
                  <div className="growth-audit-priority-action-card__validate">
                    <span className="growth-audit-priority-action-card__field-label">Come verificare</span>
                    <p>{action.howToValidate}</p>
                  </div>
                )}

                {anchor && (
                  <div className="growth-audit-priority-action-card__links">
                    <a href={`#${anchor.id}`} className="growth-audit-priority-action-card__link">
                      {anchor.label}
                    </a>
                    <span className="growth-audit-priority-action-card__rescan-note">
                      Riscansiona dopo la modifica per aggiornare score e problemi.
                    </span>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {hasHiddenActions && !compact && (
        <div className="growth-audit-priority-actions__expand">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => setShowAll((current) => !current)}
          >
            {showAll ? "Mostra meno" : `Mostra tutte (${allActions.length})`}
          </button>
        </div>
      )}
    </section>
  );
}
