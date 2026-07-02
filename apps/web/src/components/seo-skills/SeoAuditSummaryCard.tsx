import type { SeoSkillRun, SeoSkillRunResult } from "@gcr/shared";
import { buildAuditDashboardSummary, formatSeoSkillRunStatus } from "./seo-skills-utils";

interface SeoAuditSummaryCardProps {
  run: SeoSkillRun;
  results: SeoSkillRunResult[];
}

export function SeoAuditSummaryCard({ run, results }: SeoAuditSummaryCardProps) {
  const dashboard = buildAuditDashboardSummary(results);
  const statusLabel = formatSeoSkillRunStatus(run.status);
  const priorityIssues = dashboard.criticalCount + dashboard.highCount;

  return (
    <section className={`seo-audit-summary-card gcr-card seo-audit-summary-card--${dashboard.scoreBand}`}>
      <header className="seo-audit-summary-card__header">
        <div>
          <h3 className="seo-audit-summary-card__title">Riepilogo audit</h3>
          <p className="seo-audit-summary-card__meta">
            <span>{statusLabel}</span>
            <span>·</span>
            <span>{run.provider}</span>
            {run.url && (
              <>
                <span>·</span>
                <span className="seo-audit-summary-card__url">{run.url}</span>
              </>
            )}
          </p>
        </div>
        {dashboard.averageScore !== null && (
          <div className={`seo-audit-summary-card__score seo-audit-summary-card__score--${dashboard.scoreBand}`}>
            <span className="seo-audit-summary-card__score-value">{dashboard.averageScore}</span>
            <span className="seo-audit-summary-card__score-label">Score complessivo</span>
          </div>
        )}
      </header>

      <div className="seo-audit-summary-card__kpis content-seo-kpi-strip">
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value content-seo-kpi__value--warn">
            {priorityIssues}
          </span>
          <span className="content-seo-kpi__label">Problemi prioritari</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value">{dashboard.totalTasks}</span>
          <span className="content-seo-kpi__label">Task da fare</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value content-seo-kpi__value--good">
            {dashboard.completedSkills}
          </span>
          <span className="content-seo-kpi__label">Skill completate</span>
        </div>
        {dashboard.failedSkills > 0 && (
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value content-seo-kpi__value--warn">
              {dashboard.failedSkills}
            </span>
            <span className="content-seo-kpi__label">Skill fallite</span>
          </div>
        )}
      </div>

      {typeof run.progressPercent === "number" &&
        run.progressPercent < 100 &&
        (run.status === "pending" || run.status === "running") && (
          <p className="seo-audit-summary-card__progress">
            Avanzamento: {run.progressPercent}%
          </p>
        )}
    </section>
  );
}
