import type { BrandExternalSource } from "@gcr/shared";

const STATUS_LABELS: Record<string, string> = {
  pending: "In attesa",
  fetching: "Recupero in corso",
  fetched: "Recuperato",
  failed: "Non accessibile",
  skipped: "Solo URL dichiarata",
};

const TYPE_LABELS: Record<string, string> = {
  website: "Sito web",
  instagram: "Instagram",
  facebook: "Facebook",
  tiktok: "TikTok",
  youtube: "YouTube",
  linkedin: "LinkedIn",
  trustpilot: "Trustpilot",
  google_business: "Google Business",
  other: "Altra fonte",
};

interface BrandAnalyzedSourcesPanelProps {
  sources: BrandExternalSource[];
  warnings?: string[];
}

export function BrandAnalyzedSourcesPanel({
  sources,
  warnings = [],
}: BrandAnalyzedSourcesPanelProps) {
  if (!sources.length && !warnings.length) return null;

  return (
    <section className="bi-analyzed-sources">
      <h3 className="bi-panel__title">Fonti analizzate</h3>
      {sources.length === 0 ? (
        <p className="bi-panel__subtitle">Nessuna fonte esterna configurata per questo batch.</p>
      ) : (
        <ul className="bi-analyzed-sources__list">
          {sources.map((source) => (
            <li key={source.id} className="bi-analyzed-source">
              <div className="bi-analyzed-source__header">
                <span className="bi-analyzed-source__type">
                  {TYPE_LABELS[source.sourceType] ?? source.sourceType}
                  {source.label ? ` — ${source.label}` : ""}
                </span>
                <span className={`bi-analyzed-source__status bi-analyzed-source__status--${source.status}`}>
                  {STATUS_LABELS[source.status] ?? source.status}
                </span>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bi-analyzed-source__url"
              >
                {source.url}
              </a>
              {source.fetchedSummary && (
                <p className="bi-analyzed-source__summary">{source.fetchedSummary}</p>
              )}
              {source.fetchError && source.status !== "fetched" && (
                <p className="bi-analyzed-source__warning">{source.fetchError}</p>
              )}
            </li>
          ))}
        </ul>
      )}
      {warnings.length > 0 && (
        <div className="bi-analyzed-sources__batch-warnings">
          {warnings.map((w) => (
            <p key={w} className="bi-analyzed-source__warning">
              {w}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
