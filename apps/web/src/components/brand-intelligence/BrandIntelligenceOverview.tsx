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
  onStartImport: () => void;
  onGoToTab: (tab: BrandIntelligenceTab) => void;
}

export function BrandIntelligenceOverviewPanel({
  overview,
  onStartWizard,
  onStartImport,
  onGoToTab,
}: BrandIntelligenceOverviewPanelProps) {
  const { score, sections } = overview;
  const recs = score.recommendations.length > 0 ? score.recommendations : [];
  const showOnboarding = score.overallScore < 60 || !overview.hasProfile;

  return (
    <div>
      {showOnboarding && (
        <section className="bi-onboarding bi-panel" style={{ marginBottom: "1.25rem" }}>
          <h3 className="bi-panel__title">Costruisci la conoscenza del brand</h3>
          <p className="bi-panel__subtitle">
            Puoi inserire le informazioni manualmente oppure caricare documenti e lasciare che
            l&apos;AI prepari una prima bozza da revisionare.
          </p>
          <div className="bi-onboarding-cards">
            <div className="bi-onboarding-card">
              <h4 className="bi-onboarding-card__title">Compilazione guidata</h4>
              <p className="bi-onboarding-card__desc">
                Inserisci manualmente le informazioni obbligatorie minime per far partire i moduli AI.
              </p>
              <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={onStartWizard}>
                Avvia wizard manuale
              </button>
            </div>
            <div className="bi-onboarding-card">
              <h4 className="bi-onboarding-card__title">Importa da file con AI</h4>
              <p className="bi-onboarding-card__desc">
                Carica PDF, Word, cataloghi o schede prodotto. L&apos;AI estrarrà le informazioni e le
                organizzerà nelle sezioni Brand Intelligence — dovrai approvarle prima del salvataggio.
              </p>
              <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={onStartImport}>
                Carica documenti
              </button>
            </div>
          </div>
        </section>
      )}

      {(overview.pendingSectionDraftsCount ?? 0) > 0 && (
        <div className="gcr-alert gcr-alert--info" style={{ marginBottom: "1rem" }}>
          Bozze AI pronte da revisionare: {overview.pendingSectionDraftsCount} sezioni.{" "}
          <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={onStartImport}>
            Revisiona bozze Brand Intelligence
          </button>
        </div>
      )}

      {(overview.pendingFactsCount ?? 0) > 0 && (overview.pendingSectionDraftsCount ?? 0) === 0 && (
        <div className="gcr-alert" style={{ marginBottom: "1rem" }}>
          Hai {overview.pendingFactsCount} informazioni estratte da revisionare.{" "}
          <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={onStartImport}>
            Vai a Import AI
          </button>
        </div>
      )}

      <div className="bi-overview-grid">
        <div className="gcr-card bi-score-card">
          <BrandScoreRing score={score} />
          {!showOnboarding && (
            <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={onStartWizard}>
              Completa profilo
            </button>
          )}
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
    </div>
  );
}
