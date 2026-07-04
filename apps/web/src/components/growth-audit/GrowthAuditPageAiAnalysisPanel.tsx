import { useMemo, useState } from "react";
import type {
  GrowthAuditPage,
  GrowthAuditPageAiMetadata,
  GrowthAuditPageResult,
  GrowthAuditProvider,
} from "@gcr/shared";
import {
  useAnalyzeGrowthAuditPageWithAi,
  useGrowthAuditPageResults,
} from "../../hooks/useGrowthAudit";
import {
  formatGrowthAuditScore,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditSeverityBadgeClass,
  isGrowthAuditRunActive,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageAiAnalysisPanelProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
  onAnalysisComplete?: () => void;
}

type InlineFinding = {
  category?: string;
  severity?: string;
  title?: string;
  description?: string;
  evidence?: string;
  recommendation?: string;
  howToValidate?: string;
  impact?: string;
  effort?: string;
};

type InlineTask = {
  title?: string;
  description?: string;
  ownerType?: string;
  priority?: string;
  estimatedEffort?: string;
};

type InlineRecommendation = {
  title?: string;
  description?: string;
  priority?: string;
};

function getPageAiMetadata(page: GrowthAuditPage): GrowthAuditPageAiMetadata | null {
  const ai = page.metadata?.ai;
  if (!ai || typeof ai !== "object") return null;
  return ai as GrowthAuditPageAiMetadata;
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

function renderChecklist(title: string, items?: string[]) {
  if (!items || items.length === 0) return null;
  return (
    <section className="growth-audit-ai-panel__artifacts-section">
      <h5 className="growth-audit-ai-panel__artifacts-title">{title}</h5>
      <ul className="growth-audit-ai-panel__checklist">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function GrowthAuditPageAiAnalysisPanel({
  projectId,
  runId,
  page,
  runStatus,
  onAnalysisComplete,
}: GrowthAuditPageAiAnalysisPanelProps) {
  const [provider, setProvider] = useState<GrowthAuditProvider>("openai");
  const [includeSeo, setIncludeSeo] = useState(true);
  const [includeGeo, setIncludeGeo] = useState(true);
  const [includeCro, setIncludeCro] = useState(true);
  const [includeAdsReadiness, setIncludeAdsReadiness] = useState(true);
  const [feedback, setFeedback] = useState<"success" | "error" | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const pageResultsQuery = useGrowthAuditPageResults(
    projectId,
    runId,
    page.id,
    { resultType: "ai_deep_analysis" },
    true,
  );
  const analyzeMutation = useAnalyzeGrowthAuditPageWithAi(projectId, runId);

  const latestResult = useMemo(
    () => getLatestCompletedResult(pageResultsQuery.data ?? []),
    [pageResultsQuery.data],
  );
  const pageAiMeta = getPageAiMetadata(page);
  const rawOutput = latestResult?.rawOutput as Record<string, unknown> | undefined;

  const canAnalyze =
    page.status === "analyzed" &&
    !isGrowthAuditRunActive(runStatus) &&
    !analyzeMutation.isPending;

  async function handleAnalyze() {
    setFeedback(null);
    setFeedbackMessage(null);
    try {
      const response = await analyzeMutation.mutateAsync({
        pageId: page.id,
        payload: {
          provider,
          depth: "standard",
          includeSeo,
          includeGeo,
          includeCro,
          includeAdsReadiness,
        },
      });
      setFeedback("success");
      setFeedbackMessage(response.message);
      onAnalysisComplete?.();
    } catch (error) {
      setFeedback("error");
      setFeedbackMessage(
        error instanceof Error ? error.message : "Analisi AI non riuscita. Riprova.",
      );
    }
  }

  const scoreItems = [
    { label: "Score AI", value: latestResult?.score ?? pageAiMeta?.latestScore },
    { label: "SEO", value: (rawOutput?.seoScore as number | undefined) ?? pageAiMeta?.seoScore },
    { label: "GEO", value: (rawOutput?.geoScore as number | undefined) ?? page.geoScore ?? pageAiMeta?.geoScore },
    { label: "CRO", value: (rawOutput?.croScore as number | undefined) ?? page.croScore ?? pageAiMeta?.croScore },
    {
      label: "Ads readiness",
      value:
        (rawOutput?.adsReadinessScore as number | undefined) ?? pageAiMeta?.adsReadinessScore,
    },
  ];

  const findings = (latestResult?.findings ?? []) as InlineFinding[];
  const tasks = (latestResult?.tasks ?? []) as InlineTask[];
  const recommendations = (latestResult?.recommendations ?? []) as InlineRecommendation[];
  const artifacts = latestResult?.artifacts as Record<string, string[] | undefined> | undefined;

  return (
    <div className="growth-audit-ai-panel">
      <section className="growth-audit-page-drawer__section">
        <h4 className="growth-audit-page-drawer__section-title">Analisi AI/GEO/CRO</h4>
        <p className="growth-audit-ai-panel__intro">
          Analisi manuale per pagine prioritarie. Valuta SEO, GEO, CRO e readiness ads con
          metodologie euristiche — non sostituisce dati comportamentali reali.
        </p>
        <p className="growth-audit-ai-panel__cost-note">
          Usa questa funzione solo sulle pagine ad alto impatto per contenere i costi AI.
        </p>
      </section>

      <section className="growth-audit-ai-panel__form">
        <label className="growth-audit-ai-panel__field">
          <span className="growth-audit-ai-panel__field-label">Provider</span>
          <select
            className="gcr-input"
            value={provider}
            onChange={(event) => setProvider(event.target.value as GrowthAuditProvider)}
            disabled={analyzeMutation.isPending}
          >
            <option value="openai">OpenAI</option>
            <option value="claude">Claude</option>
          </select>
        </label>

        <fieldset className="growth-audit-ai-panel__areas">
          <legend className="growth-audit-ai-panel__field-label">Aree da analizzare</legend>
          <label className="growth-audit-ai-panel__checkbox">
            <input
              type="checkbox"
              checked={includeSeo}
              onChange={(event) => setIncludeSeo(event.target.checked)}
              disabled={analyzeMutation.isPending}
            />
            SEO
          </label>
          <label className="growth-audit-ai-panel__checkbox">
            <input
              type="checkbox"
              checked={includeGeo}
              onChange={(event) => setIncludeGeo(event.target.checked)}
              disabled={analyzeMutation.isPending}
            />
            GEO
          </label>
          <label className="growth-audit-ai-panel__checkbox">
            <input
              type="checkbox"
              checked={includeCro}
              onChange={(event) => setIncludeCro(event.target.checked)}
              disabled={analyzeMutation.isPending}
            />
            CRO
          </label>
          <label className="growth-audit-ai-panel__checkbox">
            <input
              type="checkbox"
              checked={includeAdsReadiness}
              onChange={(event) => setIncludeAdsReadiness(event.target.checked)}
              disabled={analyzeMutation.isPending}
            />
            Ads readiness
          </label>
        </fieldset>

        <button
          type="button"
          className="gcr-btn gcr-btn--primary gcr-btn--sm"
          disabled={!canAnalyze}
          onClick={() => void handleAnalyze()}
        >
          {analyzeMutation.isPending ? "Analisi AI in corso…" : "Analizza questa pagina"}
        </button>

        {isGrowthAuditRunActive(runStatus) && (
          <p className="growth-audit-ai-panel__warning" role="status">
            L&apos;analisi AI non è disponibile mentre il run è in corso.
          </p>
        )}
        {page.status !== "analyzed" && (
          <p className="growth-audit-ai-panel__warning" role="status">
            Completa prima la scansione tecnica della pagina.
          </p>
        )}
      </section>

      {analyzeMutation.isPending && (
        <p className="growth-audit-ai-panel__loading" role="status">
          Analisi AI in corso…
        </p>
      )}

      {feedback === "success" && feedbackMessage && (
        <div className="growth-audit-ai-panel__success" role="status">
          {feedbackMessage}
        </div>
      )}

      {feedback === "error" && feedbackMessage && (
        <div className="growth-audit-ai-panel__error" role="alert">
          {feedbackMessage}
        </div>
      )}

      {pageResultsQuery.isLoading ? (
        <p className="growth-audit-page-drawer__empty">Caricamento risultati AI…</p>
      ) : !latestResult ? (
        <p className="growth-audit-page-drawer__empty">
          Non hai ancora analizzato questa pagina con AI/GEO/CRO.
        </p>
      ) : (
        <div className="growth-audit-ai-panel__results">
          <div className="growth-audit-ai-panel__score-grid">
            {scoreItems.map((item) => (
              <div key={item.label} className="growth-audit-ai-panel__score-item">
                <span className={getGrowthAuditScoreBadgeClass(item.value)}>
                  {formatGrowthAuditScore(item.value)}
                </span>
                <span className="growth-audit-ai-panel__score-label">{item.label}</span>
              </div>
            ))}
          </div>

          {latestResult.summary && (
            <section className="growth-audit-page-drawer__section">
              <h4 className="growth-audit-page-drawer__section-title">Sintesi</h4>
              <p>{latestResult.summary}</p>
            </section>
          )}

          {findings.length > 0 && (
            <section className="growth-audit-page-drawer__section">
              <h4 className="growth-audit-page-drawer__section-title">Findings AI</h4>
              <ul className="growth-audit-page-findings">
                {findings.map((finding, index) => (
                  <li
                    key={`${finding.title ?? "finding"}-${index}`}
                    className={`growth-audit-page-finding growth-audit-page-finding--${finding.severity ?? "medium"}`}
                  >
                    <div className="growth-audit-page-finding__header">
                      {finding.severity && (
                        <span className={getGrowthAuditSeverityBadgeClass(finding.severity)}>
                          {finding.severity}
                        </span>
                      )}
                      {finding.category && (
                        <span className="growth-audit-ai-panel__category-badge">
                          {finding.category}
                        </span>
                      )}
                    </div>
                    {finding.title && (
                      <strong className="growth-audit-page-finding__title">{finding.title}</strong>
                    )}
                    {finding.description && <p>{finding.description}</p>}
                    {finding.recommendation && (
                      <p className="growth-audit-page-finding__recommendation">
                        {finding.recommendation}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {tasks.length > 0 && (
            <section className="growth-audit-page-drawer__section">
              <h4 className="growth-audit-page-drawer__section-title">Task suggeriti</h4>
              <ul className="growth-audit-ai-panel__tasks">
                {tasks.map((task, index) => (
                  <li key={`${task.title ?? "task"}-${index}`} className="growth-audit-ai-panel__task">
                    <strong>{task.title}</strong>
                    {task.description && <p>{task.description}</p>}
                    <div className="growth-audit-ai-panel__task-meta">
                      {task.ownerType && <span>Owner: {task.ownerType}</span>}
                      {task.priority && <span>Priorità: {task.priority}</span>}
                      {task.estimatedEffort && <span>Sforzo: {task.estimatedEffort}</span>}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {recommendations.length > 0 && (
            <section className="growth-audit-page-drawer__section">
              <h4 className="growth-audit-page-drawer__section-title">Raccomandazioni</h4>
              <ul className="growth-audit-ai-panel__recommendations">
                {recommendations.map((rec, index) => (
                  <li key={`${rec.title ?? "rec"}-${index}`}>
                    <strong>{rec.title}</strong>
                    {rec.description && <p>{rec.description}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {artifacts && (
            <section className="growth-audit-page-drawer__section growth-audit-ai-panel__artifacts">
              <h4 className="growth-audit-page-drawer__section-title">Checklist e note</h4>
              {renderChecklist("Hint modifica Shopify", artifacts.shopifyEditHints)}
              {renderChecklist("Checklist CRO", artifacts.croChecklist)}
              {renderChecklist("Checklist GEO", artifacts.geoChecklist)}
              {renderChecklist("Note Ads readiness", artifacts.adsReadinessNotes)}
            </section>
          )}
        </div>
      )}
    </div>
  );
}
