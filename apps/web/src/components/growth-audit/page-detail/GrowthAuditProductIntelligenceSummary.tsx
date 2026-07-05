import { useMemo } from "react";
import type {
  GrowthAuditFinding,
  GrowthAuditPage,
  GrowthAuditPageResult,
  GrowthAuditTask,
} from "@gcr/shared";
import {
  buildGrowthAuditProductIntelligenceSummary,
  getGrowthAuditProductIntelligenceLevelBadgeClass,
  getGrowthAuditProductIntelligenceLevelLabel,
  type GrowthAuditPriorityAction,
  type GrowthAuditProductIntelligenceSignal,
} from "../../../lib/growth-audit-utils";

export interface GrowthAuditProductIntelligenceSummaryProps {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  priorityActions: GrowthAuditPriorityAction[];
  aiResults?: GrowthAuditPageResult[];
  performanceResults?: GrowthAuditPageResult[];
}

function getSignalClassName(signal: GrowthAuditProductIntelligenceSignal): string {
  return `growth-audit-product-intelligence__signal growth-audit-product-intelligence__signal--${signal.tone}`;
}

export function GrowthAuditProductIntelligenceSummary({
  page,
  findings,
  tasks,
  priorityActions,
  aiResults,
  performanceResults,
}: GrowthAuditProductIntelligenceSummaryProps) {
  const summary = useMemo(
    () =>
      buildGrowthAuditProductIntelligenceSummary({
        page,
        findings,
        tasks,
        priorityActions,
        aiResults,
        performanceResults,
      }),
    [page, findings, tasks, priorityActions, aiResults, performanceResults],
  );

  if (!summary.available) {
    return null;
  }

  return (
    <section
      id="product-intelligence"
      className="growth-audit-product-intelligence growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-product-intelligence__header">
        <div className="growth-audit-product-intelligence__header-main">
          <h2 className="growth-audit-workspace-section__title">Product Intelligence</h2>
          <p className="growth-audit-workspace-section__subtitle">
            Questo blocco unisce dati tecnici, organici, analytics, performance e AI per capire se
            questa pagina prodotto merita intervento prioritario.
          </p>
        </div>
        <span className={getGrowthAuditProductIntelligenceLevelBadgeClass(summary.level)}>
          {getGrowthAuditProductIntelligenceLevelLabel(summary.level)}
        </span>
      </header>

      <div className="growth-audit-product-intelligence__hero">
        <div className="growth-audit-product-intelligence__score">
          <span className="growth-audit-product-intelligence__score-value">{summary.score}</span>
          <span className="growth-audit-product-intelligence__score-label">Product Priority Score</span>
        </div>
        <div className="growth-audit-product-intelligence__verdict">
          <h3 className="growth-audit-product-intelligence__verdict-title">{summary.title}</h3>
          <p className="growth-audit-product-intelligence__verdict-text">{summary.verdict}</p>
          <p className="growth-audit-product-intelligence__verdict-reason">{summary.mainReason}</p>
        </div>
      </div>

      {summary.evidence.length > 0 && (
        <div
          className="growth-audit-product-intelligence__signals"
          aria-label="Segnali chiave"
        >
          {summary.evidence.map((signal) => (
            <div key={signal.key} className={getSignalClassName(signal)}>
              <span className="growth-audit-product-intelligence__signal-label">{signal.label}</span>
              <strong className="growth-audit-product-intelligence__signal-value">{signal.value}</strong>
              <p className="growth-audit-product-intelligence__signal-explanation">
                {signal.explanation}
              </p>
            </div>
          ))}
        </div>
      )}

      {summary.recommendedActions.length > 0 && (
        <div className="growth-audit-product-intelligence__actions">
          <h3 className="growth-audit-product-intelligence__actions-title">Azioni consigliate</h3>
          <ul className="growth-audit-product-intelligence__actions-list">
            {summary.recommendedActions.map((action) => (
              <li key={action.title} className="growth-audit-product-intelligence__action">
                <h4 className="growth-audit-product-intelligence__action-title">{action.title}</h4>
                <p className="growth-audit-product-intelligence__action-reason">{action.reason}</p>
                <p className="growth-audit-product-intelligence__action-impact">
                  Impatto atteso: {action.expectedImpact}
                </p>
                <p className="growth-audit-product-intelligence__action-where">
                  Dove: {action.whereToFix}
                </p>
                <p className="growth-audit-product-intelligence__action-validate">
                  Come validare: {action.howToValidate}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.missingData.length > 0 && (
        <div className="growth-audit-product-intelligence__missing" role="status">
          <p className="growth-audit-product-intelligence__missing-title">
            Dati da completare: {summary.missingData.join(", ")}
          </p>
          <p className="growth-audit-product-intelligence__missing-copy">
            Più dati completi = priorità più affidabile.
          </p>
        </div>
      )}
    </section>
  );
}
