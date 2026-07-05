import { useMemo } from "react";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditRunSummary, GrowthAuditTask } from "@gcr/shared";
import {
  buildGrowthAuditAiCoverageStats,
  buildGrowthAuditPagePriorityItems,
  buildGrowthAuditSiteIssueClusters,
  formatGrowthAuditScore,
  getGrowthAuditScoreBadgeClass,
} from "../../lib/growth-audit-utils";
import { GrowthAuditAiCoveragePanel } from "./GrowthAuditAiCoveragePanel";
import { GrowthAuditSiteIssueClustersPanel } from "./GrowthAuditSiteIssueClustersPanel";
import { GrowthAuditTopPagesPanel } from "./GrowthAuditTopPagesPanel";

interface GrowthAuditPriorityDashboardProps {
  projectId: string;
  runId: string;
  pages: GrowthAuditPage[];
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  summary?: GrowthAuditRunSummary | null;
  siteScore?: number | null;
}

export function GrowthAuditPriorityDashboard({
  projectId,
  runId,
  pages,
  findings,
  tasks,
  summary,
  siteScore,
}: GrowthAuditPriorityDashboardProps) {
  const priorityItems = useMemo(
    () => buildGrowthAuditPagePriorityItems({ pages, findings, tasks }),
    [pages, findings, tasks],
  );

  const clusters = useMemo(
    () => buildGrowthAuditSiteIssueClusters(findings, tasks),
    [findings, tasks],
  );

  const aiCoverage = useMemo(
    () => buildGrowthAuditAiCoverageStats(pages, summary),
    [pages, summary],
  );

  const criticalPages = priorityItems.filter((item) => item.priorityLevel === "critical").length;
  const highPages = priorityItems.filter((item) => item.priorityLevel === "high").length;
  const openFindingsCount = findings.filter((f) => f.status === "open").length;

  return (
    <section className="growth-audit-priority-dashboard gcr-card gcr-card--glow">
      <header className="growth-audit-priority-dashboard__header">
        <h2 className="growth-audit-priority-dashboard__title">Priorità Growth Audit</h2>
        <p className="growth-audit-priority-dashboard__subtitle">
          Parti dalle pagine con maggiore impatto potenziale su SEO, conversione e ads.
        </p>
      </header>

      <div className="growth-audit-priority-dashboard__health-strip" aria-label="Riepilogo stato sito">
        <div className="growth-audit-priority-dashboard__health-item">
          <span className="growth-audit-priority-dashboard__health-label">Score tecnico</span>
          {siteScore != null ? (
            <span className={getGrowthAuditScoreBadgeClass(siteScore)}>
              {formatGrowthAuditScore(siteScore)}
            </span>
          ) : (
            <span className="growth-audit-priority-dashboard__health-value">—</span>
          )}
        </div>
        <div className="growth-audit-priority-dashboard__health-item">
          <span className="growth-audit-priority-dashboard__health-label">Pagine critiche/alte</span>
          <span className="growth-audit-priority-dashboard__health-value">
            {criticalPages + highPages}
          </span>
        </div>
        <div className="growth-audit-priority-dashboard__health-item">
          <span className="growth-audit-priority-dashboard__health-label">Problemi aperti</span>
          <span className="growth-audit-priority-dashboard__health-value">{openFindingsCount}</span>
        </div>
        <div className="growth-audit-priority-dashboard__health-item">
          <span className="growth-audit-priority-dashboard__health-label">Copertura AI</span>
          <span className="growth-audit-priority-dashboard__health-value">
            {aiCoverage.coveragePercent}%
          </span>
        </div>
      </div>

      <div className="growth-audit-priority-dashboard__grid">
        <GrowthAuditTopPagesPanel
          projectId={projectId}
          runId={runId}
          items={priorityItems}
        />
        <div className="growth-audit-priority-dashboard__side">
          <GrowthAuditSiteIssueClustersPanel clusters={clusters} />
          <GrowthAuditAiCoveragePanel stats={aiCoverage} />
        </div>
      </div>
    </section>
  );
}
