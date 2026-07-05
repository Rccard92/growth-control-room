import type { GrowthAuditPage, GrowthAuditPageAnalyticsMetadata } from "@gcr/shared";
import { getGrowthAuditPageAnalyticsMetadata } from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceAnalyticsSectionProps {
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

function formatDuration(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toFixed(0)}s`;
}

function formatCurrency(value?: number | null): string {
  if (value == null) return "—";
  return value.toFixed(2);
}

function renderOpportunity(meta: GrowthAuditPageAnalyticsMetadata, page: GrowthAuditPage): string | null {
  const sessions = meta.sessions ?? 0;
  const engagementRate = meta.engagementRate ?? 0;
  const conversions = meta.conversions ?? 0;
  const revenue = meta.revenue ?? 0;
  const pageType = (page.pageType ?? "").toLowerCase();

  if (sessions >= 50 && engagementRate < 0.4) {
    return "Traffico elevato con engagement basso: migliora above-the-fold e allineamento intent.";
  }
  if (sessions >= 30 && conversions === 0) {
    return "Traffico GA4 senza conversioni: rivedi CTA, proof e frizione.";
  }
  if (pageType === "product" && sessions >= 30 && revenue < 1) {
    return "Prodotto con sessioni ma pochi acquisti/conversioni.";
  }
  return null;
}

export function GrowthAuditPageWorkspaceAnalyticsSection({
  page,
}: GrowthAuditPageWorkspaceAnalyticsSectionProps) {
  const analyticsMeta = getGrowthAuditPageAnalyticsMetadata(page);
  const opportunity = analyticsMeta ? renderOpportunity(analyticsMeta, page) : null;

  return (
    <section
      id="analytics"
      className="growth-audit-analytics-workspace growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Google Analytics 4</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Performance post-click: sessioni, engagement e conversioni sincronizzate da GA4.
        </p>
      </header>

      {analyticsMeta ? (
        <div className="growth-audit-analytics-panel">
          <div className="growth-audit-analytics-panel__metrics">
            <div>
              <span>Sessioni</span>
              <strong>{formatNumber(analyticsMeta.sessions)}</strong>
            </div>
            <div>
              <span>Utenti</span>
              <strong>{formatNumber(analyticsMeta.totalUsers)}</strong>
            </div>
            <div>
              <span>Sessioni coinvolte</span>
              <strong>{formatNumber(analyticsMeta.engagedSessions)}</strong>
            </div>
            <div>
              <span>Engagement rate</span>
              <strong>{formatPercent(analyticsMeta.engagementRate)}</strong>
            </div>
            <div>
              <span>Durata media sessione</span>
              <strong>{formatDuration(analyticsMeta.averageSessionDuration)}</strong>
            </div>
            <div>
              <span>Conversioni</span>
              <strong>{formatNumber(analyticsMeta.conversions)}</strong>
            </div>
            <div>
              <span>Revenue</span>
              <strong>{formatCurrency(analyticsMeta.revenue)}</strong>
            </div>
          </div>

          {opportunity && (
            <p className="growth-audit-analytics-panel__opportunity">{opportunity}</p>
          )}
        </div>
      ) : (
        <p className="growth-audit-analytics-panel__empty">
          Questa pagina non ha ancora dati GA4 nella run attuale.
        </p>
      )}
    </section>
  );
}
