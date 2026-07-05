import { useMemo, useState } from "react";
import type { GrowthAuditPage, GrowthAuditPagePerformanceMetadata, GrowthAuditPageResult } from "@gcr/shared";
import {
  useAnalyzeGrowthAuditPagePerformance,
  useGrowthAuditPageResults,
} from "../../hooks/useGrowthAudit";
import {
  formatGrowthAuditScore,
  getGrowthAuditScoreBadgeClass,
  isGrowthAuditRunActive,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPagePerformanceAnalysisPanelProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
  onAnalysisComplete?: () => void;
}

type PerformanceArtifacts = {
  pagespeed?: {
    performanceScore?: number | null;
    accessibilityScore?: number | null;
    bestPracticesScore?: number | null;
    seoLighthouseScore?: number | null;
    lcp?: number | null;
    cls?: number | null;
    tbt?: number | null;
    fcp?: number | null;
    speedIndex?: number | null;
    interactive?: number | null;
    audits?: Array<Record<string, unknown>>;
  };
  crux?: {
    source?: string;
    lcpP75?: number | null;
    clsP75?: number | null;
    inpP75?: number | null;
    fcpP75?: number | null;
    ttfbP75?: number | null;
    ratings?: Record<string, string | null | undefined>;
  };
  strategy?: string;
};

function getPagePerformanceMetadata(page: GrowthAuditPage): GrowthAuditPagePerformanceMetadata | null {
  const performance = page.metadata?.performance;
  if (!performance || typeof performance !== "object") return null;
  return performance as GrowthAuditPagePerformanceMetadata;
}

function getLatestCompletedResult(results: GrowthAuditPageResult[]): GrowthAuditPageResult | null {
  const completed = results.filter((result) => result.status === "completed");
  if (completed.length === 0) return null;
  return completed.sort((a, b) => {
    const aTime = a.completedAt ?? a.createdAt ?? "";
    const bTime = b.completedAt ?? b.createdAt ?? "";
    return bTime.localeCompare(aTime);
  })[0];
}

function formatMetric(value?: number | null, unit = ""): string {
  if (value == null) return "—";
  if (unit === "ms") return `${Math.round(value)} ms`;
  if (unit === "s") return `${(value / 1000).toFixed(2)} s`;
  return String(value);
}

export function GrowthAuditPagePerformanceAnalysisPanel({
  projectId,
  runId,
  page,
  runStatus,
  onAnalysisComplete,
}: GrowthAuditPagePerformanceAnalysisPanelProps) {
  const [strategy, setStrategy] = useState<"mobile" | "desktop">("mobile");
  const [feedback, setFeedback] = useState<"success" | "error" | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const pageResultsQuery = useGrowthAuditPageResults(
    projectId,
    runId,
    page.id,
    { resultType: "performance" },
    true,
  );
  const analyzeMutation = useAnalyzeGrowthAuditPagePerformance(projectId, runId);

  const latestResult = useMemo(
    () => getLatestCompletedResult(pageResultsQuery.data ?? []),
    [pageResultsQuery.data],
  );
  const pagePerformanceMeta = getPagePerformanceMetadata(page);
  const artifacts = latestResult?.artifacts as PerformanceArtifacts | undefined;
  const pagespeed = artifacts?.pagespeed;
  const crux = artifacts?.crux;

  const canAnalyze = Boolean(page.url) && !isGrowthAuditRunActive(runStatus) && !analyzeMutation.isPending;

  async function handleAnalyze() {
    setFeedback(null);
    setFeedbackMessage(null);
    try {
      const response = await analyzeMutation.mutateAsync({
        pageId: page.id,
        payload: { strategy },
      });
      setFeedback("success");
      setFeedbackMessage(response.message);
      onAnalysisComplete?.();
    } catch (error) {
      setFeedback("error");
      setFeedbackMessage(
        error instanceof Error ? error.message : "Analisi performance non riuscita.",
      );
    }
  }

  return (
    <div className="growth-audit-performance-panel">
      <div className="growth-audit-performance-panel__controls">
        <label className="growth-audit-performance-panel__field">
          <span>Strategia</span>
          <select
            value={strategy}
            onChange={(event) => setStrategy(event.target.value as "mobile" | "desktop")}
            disabled={analyzeMutation.isPending}
          >
            <option value="mobile">Mobile</option>
            <option value="desktop">Desktop</option>
          </select>
        </label>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={!canAnalyze}
          onClick={() => void handleAnalyze()}
        >
          {analyzeMutation.isPending ? "Analisi in corso…" : "Analizza performance"}
        </button>
      </div>

      {feedback && feedbackMessage && (
        <div
          className={`gcr-alert ${feedback === "success" ? "gcr-alert--success" : "gcr-alert--error"}`}
        >
          {feedbackMessage}
        </div>
      )}

      {latestResult ? (
        <div className="growth-audit-performance-panel__results">
          <div className="growth-audit-performance-panel__score-grid">
            <div className="growth-audit-performance-panel__score-card">
              <span className="growth-audit-performance-panel__score-label">Performance Score</span>
              <span className={getGrowthAuditScoreBadgeClass(latestResult.score)}>
                {formatGrowthAuditScore(latestResult.score ?? pagePerformanceMeta?.latestScore)}
              </span>
            </div>
            <div className="growth-audit-performance-panel__score-card">
              <span className="growth-audit-performance-panel__score-label">Accessibility</span>
              <strong>{pagespeed?.accessibilityScore ?? "—"}</strong>
            </div>
            <div className="growth-audit-performance-panel__score-card">
              <span className="growth-audit-performance-panel__score-label">Best Practices</span>
              <strong>{pagespeed?.bestPracticesScore ?? "—"}</strong>
            </div>
            <div className="growth-audit-performance-panel__score-card">
              <span className="growth-audit-performance-panel__score-label">Lighthouse SEO</span>
              <strong>{pagespeed?.seoLighthouseScore ?? "—"}</strong>
            </div>
          </div>

          <div className="growth-audit-performance-panel__metrics">
            <div><span>LCP</span><strong>{formatMetric(pagespeed?.lcp, "ms")}</strong></div>
            <div><span>CLS</span><strong>{pagespeed?.cls != null ? pagespeed.cls.toFixed(3) : "—"}</strong></div>
            <div><span>INP (CrUX)</span><strong>{formatMetric(crux?.inpP75, "ms")}</strong></div>
            <div><span>TBT</span><strong>{formatMetric(pagespeed?.tbt, "ms")}</strong></div>
            <div><span>FCP</span><strong>{formatMetric(pagespeed?.fcp, "ms")}</strong></div>
          </div>

          {crux?.source === "missing" ? (
            <p className="growth-audit-performance-panel__crux-missing">
              CrUX non ha dati sufficienti per questa URL. Verranno usati i dati Lighthouse lab.
            </p>
          ) : crux?.source ? (
            <p className="growth-audit-performance-panel__crux-source">
              Dati CrUX disponibili ({crux.source === "origin" ? "livello origin" : "livello URL"}).
            </p>
          ) : null}

          {latestResult.summary && (
            <p className="growth-audit-performance-panel__summary">{latestResult.summary}</p>
          )}

          {(latestResult.findings?.length ?? 0) > 0 && (
            <section className="growth-audit-performance-panel__list-section">
              <h4>Problemi performance</h4>
              <ul>
                {(latestResult.findings as Array<Record<string, string>>).map((finding) => (
                  <li key={finding.title}>
                    <strong>{finding.title}</strong>
                    {finding.description ? ` — ${finding.description}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(latestResult.tasks?.length ?? 0) > 0 && (
            <section className="growth-audit-performance-panel__list-section">
              <h4>Task performance</h4>
              <ul>
                {(latestResult.tasks as Array<Record<string, string>>).map((task) => (
                  <li key={task.title}>
                    <strong>{task.title}</strong>
                    {task.ownerType ? ` (${task.ownerType})` : ""}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(latestResult.recommendations?.length ?? 0) > 0 && (
            <section className="growth-audit-performance-panel__list-section">
              <h4>Come risolvere</h4>
              <ul>
                {(latestResult.recommendations as Array<Record<string, string>>).map((item) => (
                  <li key={item.title}>
                    <strong>{item.title}</strong>
                    {item.description ? ` — ${item.description}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      ) : (
        <p className="growth-audit-performance-panel__empty">
          Nessuna analisi performance ancora eseguita per questa pagina.
        </p>
      )}
    </div>
  );
}
