import type { BrandIntelligenceOverview } from "@gcr/shared";
import { BrandScoreRing } from "./BrandScoreRing";

interface BrandIntelligenceOverviewPanelProps {
  overview: BrandIntelligenceOverview;
  onGoToProfile: () => void;
}

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

export function BrandIntelligenceOverviewPanel({
  overview,
  onGoToProfile,
}: BrandIntelligenceOverviewPanelProps) {
  const { score } = overview;
  const isComplete = overview.profileComplete ?? false;
  const statusLabel = isComplete ? "Completo" : overview.hasProfile ? "Incompleto" : "Non creato";

  return (
    <div>
      <section className="bi-overview-grid">
        <div className="bi-overview-score gcr-card">
          <BrandScoreRing score={score} />
          <div className="bi-overview-score__meta">
            <h3 className="bi-panel__title">Brand Profile</h3>
            <p className="bi-panel__subtitle">
              Stato: <strong>{statusLabel}</strong>
            </p>
            {overview.brandName && (
              <p className="bi-overview-field">
                <span className="bi-overview-field__label">Brand</span>
                {overview.brandName}
              </p>
            )}
            {overview.websiteUrl && (
              <p className="bi-overview-field">
                <span className="bi-overview-field__label">Sito</span>
                <a href={overview.websiteUrl} target="_blank" rel="noreferrer">
                  {overview.websiteUrl}
                </a>
              </p>
            )}
            <p className="bi-overview-field">
              <span className="bi-overview-field__label">Ultimo aggiornamento</span>
              {formatDate(overview.lastUpdated)}
            </p>
            {overview.enrichmentConfidence != null && (
              <p className="bi-overview-field">
                <span className="bi-overview-field__label">Confidence enrich</span>
                {Math.round(overview.enrichmentConfidence * 100)}%
              </p>
            )}
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              style={{ marginTop: "0.75rem" }}
              onClick={onGoToProfile}
            >
              {overview.hasProfile ? "Aggiorna Brand Profile" : "Crea Brand Profile"}
            </button>
          </div>
        </div>

        <div className="bi-panel gcr-card">
          <h3 className="bi-panel__title">Raccomandazioni</h3>
          {score.recommendations.length > 0 ? (
            <ul className="bi-recommendations">
              {score.recommendations.map((rec) => (
                <li key={rec}>{rec}</li>
              ))}
            </ul>
          ) : (
            <p className="bi-panel__subtitle">Il profilo brand è pronto per i moduli AI.</p>
          )}
        </div>
      </section>

      {(overview.enrichmentWarnings?.length ?? 0) > 0 && (
        <div className="gcr-alert gcr-alert--warning" style={{ marginTop: "1rem" }}>
          <strong>Avvisi enrich:</strong>
          <ul>
            {overview.enrichmentWarnings!.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {score.missingRequired.length > 0 && (
        <div className="gcr-alert gcr-alert--info" style={{ marginTop: "1rem" }}>
          Campi mancanti: {score.missingRequired.join(", ")}
        </div>
      )}
    </div>
  );
}
