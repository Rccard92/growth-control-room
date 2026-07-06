import { useMemo, useState } from "react";
import type { GrowthAuditPage, GrowthAuditPageKeywordIntelligenceMetadata, GrowthAuditKeywordSearchVolumeItem } from "@gcr/shared";
import { useAnalyzeGrowthAuditPageKeywordIntelligence } from "../../hooks/useGrowthAudit";
import { useDataForSeoStatus, useDataForSeoUsage } from "../../hooks/useDataForSeo";
import { formatTrend } from "../../lib/dataforseo-sandbox-utils";
import {
  buildKeywordIntelligenceCostEstimate,
  formatKeywordIntelligenceCostEstimateNote,
  formatKeywordIntelligenceAnalysisError,
  getGrowthAuditPageKeywordIntelligenceMetadata,
  isGrowthAuditRunActive,
  isKeywordIntelligenceFresh,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageKeywordIntelligencePanelProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
}

function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(4)}`;
}

function formatNumber(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString("it-IT");
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

export function GrowthAuditPageKeywordIntelligencePanel({
  projectId,
  runId,
  page,
  runStatus,
}: GrowthAuditPageKeywordIntelligencePanelProps) {
  const [maxSeedQueries, setMaxSeedQueries] = useState(10);
  const [keywordIdeasSeeds, setKeywordIdeasSeeds] = useState(1);
  const [serpKeywords, setSerpKeywords] = useState(3);
  const [locationCode, setLocationCode] = useState(2380);
  const [languageCode, setLanguageCode] = useState("it");
  const [feedback, setFeedback] = useState<string | null>(null);

  const { data: dfsStatus } = useDataForSeoStatus(projectId);
  const { data: dfsUsage } = useDataForSeoUsage(projectId);
  const analyzeMutation = useAnalyzeGrowthAuditPageKeywordIntelligence(projectId, runId);

  const metadata = getGrowthAuditPageKeywordIntelligenceMetadata(page);
  const isFresh = isKeywordIntelligenceFresh(metadata);
  const costEstimate = useMemo(
    () =>
      buildKeywordIntelligenceCostEstimate(
        {
          maxSeedQueries,
          keywordIdeasSeeds,
          serpKeywords,
        },
        dfsUsage?.averageCostByOperation,
      ),
    [maxSeedQueries, keywordIdeasSeeds, serpKeywords, dfsUsage?.averageCostByOperation],
  );

  const canAnalyze =
    Boolean(page.url) &&
    !isGrowthAuditRunActive(runStatus) &&
    !analyzeMutation.isPending &&
    dfsStatus?.configured &&
    dfsStatus?.realCallsEnabled;

  const runAnalysis = async (force: boolean) => {
    setFeedback(null);
    try {
      const result = await analyzeMutation.mutateAsync({
        pageId: page.id,
        payload: {
          maxSeedQueries,
          keywordIdeasSeeds,
          serpKeywords,
          locationCode,
          languageCode,
          force,
        },
      });
      setFeedback(result.message);
    } catch (error) {
      setFeedback(formatKeywordIntelligenceAnalysisError(error));
    }
  };

  return (
    <div className="growth-audit-keyword-intelligence">
      <div className="growth-audit-keyword-intelligence__controls">
        <label className="gcr-select-label growth-audit-keyword-intelligence__field">
          <span>Max seed query</span>
          <span className="gcr-select-wrap">
            <select
              className="gcr-select"
              value={maxSeedQueries}
              onChange={(event) => setMaxSeedQueries(Number(event.target.value))}
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
            </select>
          </span>
        </label>
        <label className="gcr-select-label growth-audit-keyword-intelligence__field">
          <span>Keyword ideas seeds</span>
          <span className="gcr-select-wrap">
            <select
              className="gcr-select"
              value={keywordIdeasSeeds}
              onChange={(event) => setKeywordIdeasSeeds(Number(event.target.value))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
            </select>
          </span>
        </label>
        <label className="gcr-select-label growth-audit-keyword-intelligence__field">
          <span>SERP keywords</span>
          <span className="gcr-select-wrap">
            <select
              className="gcr-select"
              value={serpKeywords}
              onChange={(event) => setSerpKeywords(Number(event.target.value))}
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={3}>3</option>
            </select>
          </span>
        </label>
      </div>

      <details className="growth-audit-keyword-intelligence__advanced">
        <summary>Impostazioni avanzate</summary>
        <div className="growth-audit-keyword-intelligence__controls">
          <label className="gcr-field growth-audit-keyword-intelligence__field">
            <span className="gcr-field__label">Location code</span>
            <input
              className="gcr-input"
              type="number"
              value={locationCode}
              onChange={(event) => setLocationCode(Number(event.target.value))}
            />
          </label>
          <label className="gcr-field growth-audit-keyword-intelligence__field">
            <span className="gcr-field__label">Language</span>
            <input
              className="gcr-input"
              value={languageCode}
              onChange={(event) => setLanguageCode(event.target.value)}
            />
          </label>
        </div>
      </details>

      <p className="growth-audit-keyword-intelligence__warning">
        Questa analisi usa credito DataForSEO. Stima circa {formatUsd(costEstimate.totalUsd)} con le
        impostazioni attuali.
      </p>
      <p className="growth-audit-keyword-intelligence__estimate-note">
        {formatKeywordIntelligenceCostEstimateNote(costEstimate)}
      </p>

      {!dfsStatus?.realCallsEnabled && (
        <p className="growth-audit-keyword-intelligence__warning growth-audit-keyword-intelligence__warning--error">
          Le chiamate reali DataForSEO sono disabilitate sul backend.
        </p>
      )}

      {isFresh && metadata && (
        <div className="growth-audit-keyword-intelligence__fresh-banner">
          Dati recenti (sync {new Date(metadata.syncedAt ?? "").toLocaleString("it-IT")}).
          Puoi riusare i dati esistenti o forzare un aggiornamento.
        </div>
      )}

      <div className="growth-audit-keyword-intelligence__actions">
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={!canAnalyze}
          onClick={() => void runAnalysis(isFresh)}
        >
          {analyzeMutation.isPending
            ? "Analisi in corso…"
            : isFresh
              ? "Aggiorna comunque"
              : "Aggiorna Keyword Intelligence"}
        </button>
        {isFresh && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={analyzeMutation.isPending}
            onClick={() => setFeedback("Dati recenti già disponibili in questa pagina.")}
          >
            Usa dati esistenti
          </button>
        )}
      </div>

      {feedback && (
        <p className="growth-audit-keyword-intelligence__feedback" role="status">
          {feedback}
        </p>
      )}

      {metadata && <KeywordIntelligenceResults metadata={metadata} />}
    </div>
  );
}

function KeywordIntelligenceResults({
  metadata,
}: {
  metadata: GrowthAuditPageKeywordIntelligenceMetadata;
}) {
  const volumeByQuery = useMemo(() => {
    const map = new Map<string, GrowthAuditKeywordSearchVolumeItem>();
    for (const item of metadata.searchVolume ?? []) {
      map.set(item.keyword.toLowerCase(), item);
    }
    return map;
  }, [metadata.searchVolume]);

  return (
    <>
      <div className="growth-audit-keyword-intelligence__summary">
        <div>
          <span>Keyword arricchite</span>
          <strong>{metadata.searchVolume?.length ?? 0}</strong>
        </div>
        <div>
          <span>Costo run</span>
          <strong>{formatUsd(metadata.cost?.totalUsd)}</strong>
        </div>
        <div>
          <span>Competitor</span>
          <strong>{metadata.competitors?.length ?? 0}</strong>
        </div>
        <div>
          <span>SERP analizzate</span>
          <strong>{metadata.serp?.length ?? 0}</strong>
        </div>
        <div>
          <span>Ultimo sync</span>
          <strong>
            {metadata.syncedAt
              ? new Date(metadata.syncedAt).toLocaleString("it-IT")
              : "—"}
          </strong>
        </div>
      </div>

      {(metadata.seedQueries?.length ?? 0) > 0 && (
        <div className="growth-audit-keyword-intelligence__table-wrap">
          <h3>Query e volumi</h3>
          <table className="growth-audit-keyword-intelligence__table gcr-table">
            <thead>
              <tr>
                <th>Query</th>
                <th>GSC impr.</th>
                <th>CTR</th>
                <th>Pos.</th>
                <th>Volume</th>
                <th>CPC</th>
                <th>Competition</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {metadata.seedQueries?.map((seed) => {
                const volume = volumeByQuery.get(seed.query.toLowerCase());
                return (
                  <tr key={seed.query}>
                    <td>{seed.query}</td>
                    <td>{formatNumber(seed.impressions ?? null)}</td>
                    <td>{formatPercent(seed.ctr ?? null)}</td>
                    <td>{seed.position ?? "—"}</td>
                    <td>{formatNumber(volume?.searchVolume ?? null)}</td>
                    <td>{formatUsd(volume?.cpc ?? null)}</td>
                    <td>{volume?.competition ?? "—"}</td>
                    <td>{formatTrend(volume?.trend?.direction)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {(metadata.keywordIdeas?.items?.length ?? 0) > 0 && (
        <div className="growth-audit-keyword-intelligence__table-wrap">
          <h3>Keyword ideas ({metadata.keywordIdeas?.seedKeyword})</h3>
          <table className="growth-audit-keyword-intelligence__table gcr-table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Volume</th>
                <th>CPC</th>
                <th>Competition</th>
              </tr>
            </thead>
            <tbody>
              {metadata.keywordIdeas?.items?.map((idea) => (
                <tr key={idea.keyword}>
                  <td>{idea.keyword}</td>
                  <td>{formatNumber(idea.searchVolume ?? null)}</td>
                  <td>{formatUsd(idea.cpc ?? null)}</td>
                  <td>{idea.competition ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(metadata.serp?.length ?? 0) > 0 && (
        <div className="growth-audit-keyword-intelligence__serp">
          <h3>SERP competitor</h3>
          {metadata.serp?.map((serp) => (
            <div key={serp.keyword} className="growth-audit-keyword-intelligence__serp-block">
              <h4>{serp.keyword}</h4>
              {(serp.refinementChips?.length ?? 0) > 0 && (
                <div className="growth-audit-keyword-intelligence__chips">
                  {serp.refinementChips?.map((chip) => (
                    <span key={chip} className="growth-audit-keyword-intelligence__chip">
                      {chip}
                    </span>
                  ))}
                </div>
              )}
              <table className="growth-audit-keyword-intelligence__table gcr-table">
                <thead>
                  <tr>
                    <th>Pos.</th>
                    <th>Dominio</th>
                    <th>Title</th>
                    <th>URL</th>
                  </tr>
                </thead>
                <tbody>
                  {serp.topResults?.map((result, index) => (
                    <tr key={`${serp.keyword}-${result.url ?? index}`}>
                      <td>{result.position ?? "—"}</td>
                      <td>{result.domain ?? "—"}</td>
                      <td>{result.title ?? "—"}</td>
                      <td>{result.url ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}

      {(metadata.competitors?.length ?? 0) > 0 && (
        <div className="growth-audit-keyword-intelligence__competitors">
          <h3>Competitor summary</h3>
          <table className="growth-audit-keyword-intelligence__table gcr-table">
            <thead>
              <tr>
                <th>Dominio</th>
                <th>Apparizioni</th>
                <th>Miglior pos.</th>
                <th>Keyword</th>
              </tr>
            </thead>
            <tbody>
              {metadata.competitors?.map((competitor) => (
                <tr key={competitor.domain}>
                  <td>{competitor.domain}</td>
                  <td>{competitor.appearancesCount ?? 0}</td>
                  <td>{competitor.bestPosition ?? "—"}</td>
                  <td>{competitor.keywords?.join(", ") ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="growth-audit-keyword-intelligence__cost">
        <h3>Dettagli costo</h3>
        <p>Search volume: {formatUsd(metadata.cost?.searchVolumeUsd)}</p>
        <p>Keyword ideas: {formatUsd(metadata.cost?.keywordIdeasUsd)}</p>
        <p>SERP: {formatUsd(metadata.cost?.serpUsd)}</p>
        <p>
          <strong>Totale: {formatUsd(metadata.cost?.totalUsd)}</strong>
        </p>
        {(metadata.dataQuality?.warnings?.length ?? 0) > 0 && (
          <ul>
            {metadata.dataQuality?.warnings?.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
