import type { BrandIntelligenceOverview, BrandIntelligenceTab } from "@gcr/shared";
import { BrandScoreRing } from "./BrandScoreRing";

const SECTION_TAB_MAP: Record<string, BrandIntelligenceTab> = {
  brandProfile: "profile",
  voiceTone: "voice",
  productsCategories: "products",
  audience: "audience",
  claimsCompliance: "claims",
  seoStrategy: "seo",
  contentPillars: "pillars",
  aiGuardrails: "guardrails",
  assets: "assets",
};

interface BrandIntelligenceOverviewPanelProps {
  overview: BrandIntelligenceOverview;
  onStartWizard: () => void;
  onGoToTab: (tab: BrandIntelligenceTab) => void;
}

export function BrandIntelligenceOverviewPanel({
  overview,
  onStartWizard,
  onGoToTab,
}: BrandIntelligenceOverviewPanelProps) {
  const { score, sections } = overview;
  const recs = score.recommendations.length > 0 ? score.recommendations : [];

  return (
    <div className="bi-overview-grid">
      <div className="gcr-card bi-score-card">
        <BrandScoreRing score={score} />
        <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={onStartWizard}>
          {score.overallScore < 60 ? "Avvia wizard" : "Completa profilo"}
        </button>
      </div>

      <div className="bi-panel">
        <h3 className="bi-panel__title">Sezioni Brand Knowledge</h3>
        <p className="bi-panel__subtitle">
          Ogni sezione contribuisce al punteggio usato dai moduli AI per generare contenuti on-brand.
        </p>
        <div className="bi-sections-grid">
          {sections.map((section) => (
            <button
              key={section.key}
              type="button"
              className={`bi-section-card ${section.complete ? "bi-section-card--complete" : ""}`}
              onClick={() => {
                const tab = SECTION_TAB_MAP[section.key];
                if (tab) onGoToTab(tab);
              }}
            >
              <div className="bi-section-card__label">{section.label}</div>
              <div className="bi-section-card__score">
                {section.complete ? "Completa" : "Da completare"} · {section.score}%
              </div>
            </button>
          ))}
        </div>

        {recs.length > 0 && (
          <>
            <h4 style={{ marginTop: "1.25rem", marginBottom: "0.5rem", fontSize: "0.9rem" }}>
              Suggerimenti
            </h4>
            <ul className="bi-recommendations">
              {recs.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </>
        )}

        {score.missingRequired.length > 0 && (
          <>
            <h4 style={{ marginTop: "1.25rem", marginBottom: "0.5rem", fontSize: "0.9rem" }}>
              Campi obbligatori mancanti
            </h4>
            <ul className="bi-recommendations">
              {score.missingRequired.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
