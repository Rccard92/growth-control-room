import type { GrowthAuditPage, GrowthAuditPageSearchConsoleMetadata } from "@gcr/shared";
import { getGrowthAuditPageSearchConsoleMetadata } from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceSearchConsoleSectionProps {
  page: GrowthAuditPage;
}

function formatPercent(value?: number | null): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

function formatNumber(value?: number | null): string {
  if (value == null) return "—";
  return String(value);
}

function formatPosition(value?: number | null): string {
  if (value == null) return "—";
  return value.toFixed(1);
}

function renderOpportunity(meta: GrowthAuditPageSearchConsoleMetadata): string | null {
  const impressions = meta.impressions ?? 0;
  const ctr = meta.ctr ?? 0;
  const position = meta.position ?? 0;
  if (impressions >= 100 && ctr < 0.02) {
    return "Opportunità CTR: molte impression con CTR basso.";
  }
  if (position >= 4 && position <= 15 && impressions >= 20) {
    return "Opportunità posizionamento: sei vicino alla prima pagina.";
  }
  if (impressions > 0 && (meta.clicks ?? 0) === 0) {
    return "Opportunità click: la pagina compare in SERP ma non genera click.";
  }
  return null;
}

export function GrowthAuditPageWorkspaceSearchConsoleSection({
  page,
}: GrowthAuditPageWorkspaceSearchConsoleSectionProps) {
  const searchConsoleMeta = getGrowthAuditPageSearchConsoleMetadata(page);
  const opportunity = searchConsoleMeta ? renderOpportunity(searchConsoleMeta) : null;

  return (
    <section
      id="search-console"
      className="growth-audit-search-console-workspace growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Search Console</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Dati organici reali (click, impression, CTR, posizione) sincronizzati da Google Search
          Console.
        </p>
      </header>

      {searchConsoleMeta ? (
        <div className="growth-audit-search-console-panel">
          <div className="growth-audit-search-console-panel__metrics">
            <div>
              <span>Click</span>
              <strong>{formatNumber(searchConsoleMeta.clicks)}</strong>
            </div>
            <div>
              <span>Impression</span>
              <strong>{formatNumber(searchConsoleMeta.impressions)}</strong>
            </div>
            <div>
              <span>CTR</span>
              <strong>{formatPercent(searchConsoleMeta.ctr)}</strong>
            </div>
            <div>
              <span>Posizione media</span>
              <strong>{formatPosition(searchConsoleMeta.position)}</strong>
            </div>
          </div>

          {opportunity && (
            <p className="growth-audit-search-console-panel__opportunity">{opportunity}</p>
          )}

          {(searchConsoleMeta.topQueries?.length ?? 0) > 0 && (
            <section className="growth-audit-search-console-panel__queries">
              <h4>Query principali</h4>
              <ul>
                {searchConsoleMeta.topQueries?.map((query) => (
                  <li key={query.query}>
                    <strong>{query.query}</strong>
                    {" — "}
                    {query.impressions ?? 0} imp., CTR {formatPercent(query.ctr)}, pos.{" "}
                    {formatPosition(query.position)}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      ) : (
        <p className="growth-audit-search-console-panel__empty">
          Questa pagina non ha ancora dati Search Console nella run attuale.
        </p>
      )}
    </section>
  );
}
