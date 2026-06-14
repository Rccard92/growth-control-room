import type { BrandIntelligenceOverview, BrandIntelligenceTab } from "@gcr/shared";

interface BrandIntelligenceOverviewPanelProps {
  overview: BrandIntelligenceOverview;
  onOpenSection: (tab: BrandIntelligenceTab) => void;
}

const STATUS_LABELS: Record<string, string> = {
  complete: "Completo",
  partial: "Parziale",
  empty: "Da completare",
};

const TAB_BY_KEY: Record<string, BrandIntelligenceTab> = {
  brandProfile: "profile",
  brandIdentity: "identity",
  visualIdentity: "visualIdentity",
  safeClaims: "safeClaims",
  productKnowledge: "productKnowledge",
  faqObjections: "faqObjections",
  editorialGuidelines: "editorialGuidelines",
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("it-IT", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function statusClass(status: string): string {
  if (status === "complete") return "bi-module-card--complete";
  if (status === "partial") return "bi-module-card--partial";
  return "bi-module-card--empty";
}

export function BrandIntelligenceOverviewPanel({
  overview,
  onOpenSection,
}: BrandIntelligenceOverviewPanelProps) {
  const sections = overview.sections ?? [];
  const recommendations = overview.score?.recommendations ?? [];

  return (
    <div>
      <section className="bi-modules-grid">
        {sections.map((section) => {
          const tab = TAB_BY_KEY[section.key];
          return (
            <article
              key={section.key}
              className={`bi-module-card gcr-card ${statusClass(section.status)}`}
            >
              <div className="bi-module-card__header">
                <h3 className="bi-panel__title">{section.label}</h3>
                <span className={`bi-module-badge bi-module-badge--${section.status}`}>
                  {STATUS_LABELS[section.status] ?? section.status}
                </span>
              </div>
              <p className="bi-overview-field">
                <span className="bi-overview-field__label">Ultima modifica</span>
                {formatDate(section.updatedAt)}
              </p>
              {section.missingFields.length > 0 && (
                <p className="bi-overview-field">
                  <span className="bi-overview-field__label">Campi mancanti</span>
                  {section.missingFields.slice(0, 4).join(", ")}
                  {section.missingFields.length > 4 ? "…" : ""}
                </p>
              )}
              {tab && (
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                  style={{ marginTop: "0.75rem" }}
                  onClick={() => onOpenSection(tab)}
                >
                  Apri sezione
                </button>
              )}
            </article>
          );
        })}
      </section>

      {overview.brandName && (
        <p className="bi-overview-field" style={{ marginTop: "1rem" }}>
          <span className="bi-overview-field__label">Brand</span>
          {overview.brandName}
          {overview.websiteUrl && (
            <>
              {" · "}
              <a href={overview.websiteUrl} target="_blank" rel="noreferrer">
                {overview.websiteUrl}
              </a>
            </>
          )}
        </p>
      )}

      {recommendations.length > 0 && (
        <div className="bi-panel gcr-card" style={{ marginTop: "1rem" }}>
          <h3 className="bi-panel__title">Raccomandazioni</h3>
          <ul className="bi-recommendations">
            {recommendations.map((rec) => (
              <li key={rec}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
}
