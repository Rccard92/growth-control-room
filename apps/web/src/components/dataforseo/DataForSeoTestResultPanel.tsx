import type { DataForSeoTestResponse, SearchVolumeResult } from "@gcr/shared";
import { formatTrend } from "../../lib/dataforseo-sandbox-utils";

function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(4)}`;
}

function formatNumber(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString("it-IT");
}

function isSearchVolumeSummary(
  summary: Record<string, unknown> | null | undefined,
): summary is {
  results?: SearchVolumeResult[];
  keywordCount?: number;
  averageCostPerKeywordUsd?: number | null;
} {
  if (!summary) return false;
  return Array.isArray(summary.results) || summary.keywordCount != null;
}

function extractSearchVolumeRows(result: DataForSeoTestResponse): SearchVolumeResult[] {
  const summary = result.responseSummary;
  if (isSearchVolumeSummary(summary) && summary.results?.length) {
    return summary.results;
  }
  if (isSearchVolumeSummary(summary) && summary.results) {
    return summary.results;
  }
  if (summary && Array.isArray(summary.items)) {
    return summary.items as SearchVolumeResult[];
  }
  if (result.keyword) {
    return [{ keyword: result.keyword }];
  }
  return [];
}

function renderSimpleSummary(summary: Record<string, unknown>) {
  return (
    <pre className="gcr-code-block" style={{ marginTop: "0.75rem" }}>
      {JSON.stringify(summary, null, 2)}
    </pre>
  );
}

export function DataForSeoTestResultPanel({ result }: { result: DataForSeoTestResponse }) {
  const isSearchVolume =
    result.testType === "search_volume" || result.testType === "search_volume_batch";
  const rows = isSearchVolume ? extractSearchVolumeRows(result) : [];
  const keywordCount = result.keywords?.length ?? rows.length ?? 1;

  return (
    <section className="gcr-panel" style={{ marginBottom: "1.5rem" }}>
      <div className="gcr-panel__header">
        <h2 className="gcr-panel__title">Risultato test</h2>
      </div>

      <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "1rem" }}>
        <div>
          <span className="gcr-muted">Costo totale</span>
          <div>
            <strong>{formatUsd(result.costUsd)}</strong>
          </div>
        </div>
        {result.averageCostPerKeywordUsd != null && (
          <div>
            <span className="gcr-muted">Costo medio / keyword</span>
            <div>
              <strong>{formatUsd(result.averageCostPerKeywordUsd)}</strong>
            </div>
          </div>
        )}
        <div>
          <span className="gcr-muted">Keyword</span>
          <div>
            <strong>{keywordCount}</strong>
          </div>
        </div>
        <div>
          <span className="gcr-muted">Endpoint</span>
          <div>{result.endpoints.join(", ")}</div>
        </div>
      </div>

      {isSearchVolume && rows.length > 0 ? (
        <div className="gcr-table-wrap">
          <table className="gcr-table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Volume</th>
                <th>CPC</th>
                <th>Competition</th>
                <th>Index</th>
                <th>Trend</th>
                <th>Ultimo mese</th>
                <th>Media 12m</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.keyword}>
                  <td>{row.keyword}</td>
                  <td>{formatNumber(row.searchVolume)}</td>
                  <td>{formatUsd(row.cpc)}</td>
                  <td>{row.competition ?? "—"}</td>
                  <td>{row.competitionIndex ?? "—"}</td>
                  <td>{formatTrend(row.trend?.direction)}</td>
                  <td>{formatNumber(row.trend?.lastMonth)}</td>
                  <td>{formatNumber(row.trend?.averageLast12Months)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        result.responseSummary && renderSimpleSummary(result.responseSummary)
      )}

      {result.rawPreview && (
        <details style={{ marginTop: "0.75rem" }}>
          <summary>Raw response tecnica</summary>
          <pre className="gcr-code-block">
            {JSON.stringify(result.rawPreview, null, 2)}
          </pre>
        </details>
      )}
    </section>
  );
}
