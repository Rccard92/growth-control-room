import { useMemo } from "react";
import type {
  GrowthAuditFinding,
  GrowthAuditPage,
  GrowthAuditPageResult,
  GrowthAuditRunSummary,
  GrowthAuditTask,
} from "@gcr/shared";
import {
  buildGrowthAuditEconomicPriorityItem,
  buildGrowthAuditProductIntelligenceSummary,
  getGrowthAuditEconomicPriorityLevelBadgeClass,
  getGrowthAuditEconomicPriorityLevelLabel,
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
  runSummary?: GrowthAuditRunSummary | null;
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
  runSummary,
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
        runSummary,
      }),
    [page, findings, tasks, priorityActions, aiResults, performanceResults, runSummary],
  );

  const economicPriority = useMemo(
    () => buildGrowthAuditEconomicPriorityItem({ page, findings, tasks }),
    [page, findings, tasks],
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

      {economicPriority && (
        <div className="growth-audit-economic-priority__breakdown growth-audit-product-intelligence__economic">
          <header className="growth-audit-economic-priority__breakdown-header">
            <h3 className="growth-audit-economic-priority__breakdown-title">Priorità economica</h3>
            <span
              className={getGrowthAuditEconomicPriorityLevelBadgeClass(economicPriority.level)}
            >
              {getGrowthAuditEconomicPriorityLevelLabel(economicPriority.level)}
            </span>
          </header>

          <div className="growth-audit-economic-priority__breakdown-hero">
            <div className="growth-audit-economic-priority__score">
              <span className="growth-audit-economic-priority__score-value">
                {economicPriority.score}
              </span>
              <span className="growth-audit-economic-priority__score-label">
                Economic Priority Score
              </span>
            </div>
            <p className="growth-audit-economic-priority__reason">{economicPriority.shortReason}</p>
          </div>

          <div className="growth-audit-economic-priority__breakdown-grid">
            <div className="growth-audit-economic-priority__breakdown-item">
              <span>Business</span>
              <strong>{economicPriority.breakdown.businessImpact}</strong>
            </div>
            <div className="growth-audit-economic-priority__breakdown-item">
              <span>SEO opportunity</span>
              <strong>{economicPriority.breakdown.organicOpportunity}</strong>
            </div>
            <div className="growth-audit-economic-priority__breakdown-item">
              <span>GA4/Funnel</span>
              <strong>{economicPriority.breakdown.ecommerceFunnel}</strong>
            </div>
            <div className="growth-audit-economic-priority__breakdown-item">
              <span>CRO/Tech</span>
              <strong>{economicPriority.breakdown.technicalAndCroRisk}</strong>
            </div>
            <div className="growth-audit-economic-priority__breakdown-item">
              <span>Stock</span>
              <strong>{economicPriority.breakdown.stockAndAvailability}</strong>
            </div>
            <div
              className={`growth-audit-economic-priority__breakdown-item growth-audit-economic-priority__confidence${
                economicPriority.breakdown.dataConfidence < 40
                  ? " growth-audit-economic-priority__confidence--low"
                  : ""
              }`}
            >
              <span>Data confidence</span>
              <strong>{economicPriority.breakdown.dataConfidence}</strong>
            </div>
          </div>

          {economicPriority.reasons.length > 0 && (
            <ul className="growth-audit-economic-priority__reasons-list">
              {economicPriority.reasons.slice(0, 3).map((reason) => (
                <li key={reason.key} className="growth-audit-economic-priority__reason-item">
                  {reason.detail}
                </li>
              ))}
            </ul>
          )}

          {economicPriority.metrics.bestVariantTitle &&
            economicPriority.metrics.bestVariantRevenue != null && (
              <p className="growth-audit-economic-priority__variant-note">
                Variante più redditizia: {economicPriority.metrics.bestVariantTitle} ·{" "}
                {economicPriority.metrics.bestVariantRevenue.toLocaleString("it-IT", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}{" "}
                EUR
              </p>
            )}

          {economicPriority.metrics.keywordOpportunityCount != null &&
            economicPriority.metrics.keywordOpportunityCount > 0 && (
              <p className="growth-audit-economic-priority__ki-note">
                Opportunità keyword rilevate: {economicPriority.metrics.keywordOpportunityCount}
                {economicPriority.metrics.highestSearchVolume != null && (
                  <>
                    {" "}
                    · Volume max:{" "}
                    {economicPriority.metrics.highestSearchVolume.toLocaleString("it-IT")}
                  </>
                )}
                {economicPriority.metrics.topCompetitorCount != null &&
                  economicPriority.metrics.topCompetitorCount > 0 && (
                    <> · Competitor SERP: {economicPriority.metrics.topCompetitorCount}</>
                  )}
              </p>
            )}

          {economicPriority.breakdown.stockAndAvailability > 0 && (
            <p className="growth-audit-economic-priority__stock-warning" role="status">
              Attenzione: stock o disponibilità potrebbero limitare le vendite su questa pagina.
            </p>
          )}
        </div>
      )}

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
