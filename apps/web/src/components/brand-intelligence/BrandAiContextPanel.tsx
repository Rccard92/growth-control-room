import { useState } from "react";
import type { BrandContextBundle } from "@gcr/shared";
import { useBrandContext } from "../../hooks/useBrandIntelligence";

interface BrandAiContextPanelProps {
  projectId: string;
}

const SECTION_LABELS: Record<string, string> = {
  brandProfile: "Brand Profile",
  brandIdentity: "Brand Identity",
  visualIdentity: "Visual Identity",
  safeClaims: "Safe Claims",
  productKnowledge: "Product Knowledge",
  faqObjections: "FAQ & Objections",
};

function getIncludedSections(context: BrandContextBundle): string[] {
  const pc = context.promptContext;
  if (!pc) return [];
  const included: string[] = [];
  if (pc.brandProfile && pc.brandProfile.split("\n").length > 1) {
    included.push(SECTION_LABELS.brandProfile);
  }
  if (pc.brandIdentity && pc.brandIdentity.split("\n").length > 1) {
    included.push(SECTION_LABELS.brandIdentity);
  }
  if (pc.visualIdentity && pc.visualIdentity.split("\n").length > 1) {
    included.push(SECTION_LABELS.visualIdentity);
  }
  if (pc.safeClaims) included.push(SECTION_LABELS.safeClaims);
  if (pc.productKnowledge) included.push(SECTION_LABELS.productKnowledge);
  if (pc.faqObjections) included.push(SECTION_LABELS.faqObjections);
  return included;
}

function getEmptySections(context: BrandContextBundle): string[] {
  const pc = context.promptContext;
  const empty: string[] = [];
  if (!pc?.brandIdentity || pc.brandIdentity.split("\n").length <= 1) {
    empty.push(SECTION_LABELS.brandIdentity);
  }
  if (!pc?.visualIdentity || pc.visualIdentity.split("\n").length <= 1) {
    empty.push(SECTION_LABELS.visualIdentity);
  }
  if (!pc?.productKnowledge) empty.push(SECTION_LABELS.productKnowledge);
  if (!pc?.faqObjections) empty.push(SECTION_LABELS.faqObjections);
  return empty;
}

export function BrandAiContextPanel({ projectId }: BrandAiContextPanelProps) {
  const { data: context, isLoading, isFetching, refetch } = useBrandContext(projectId);
  const [copyMsg, setCopyMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewText =
    context?.promptContext?.previewText
    ?? context?.promptContext?.fullText
    ?? "";

  const included = context ? getIncludedSections(context) : [];
  const emptySections = context ? getEmptySections(context) : [];
  const missing = context?.missingContext ?? [];

  async function handleCopy() {
    if (!previewText) {
      setError("Nessun contesto da copiare.");
      return;
    }
    setError(null);
    try {
      await navigator.clipboard.writeText(previewText);
      setCopyMsg("Contesto copiato negli appunti.");
      setTimeout(() => setCopyMsg(null), 2500);
    } catch {
      setError("Impossibile copiare il contesto.");
    }
  }

  if (isLoading) {
    return <p className="bi-panel__subtitle">Caricamento contesto AI…</p>;
  }

  if (!context || context.primarySource === "minimal") {
    return (
      <div className="bi-profile-v1">
        <p className="bi-panel__subtitle">
          Compila almeno il Brand Profile per generare il contesto AI.
        </p>
      </div>
    );
  }

  return (
    <div className="bi-profile-v1">
      <p className="bi-panel__subtitle" style={{ marginBottom: "1.25rem" }}>
        Questo è il contesto che i moduli AI useranno per generare SEO, PED, Ads, Email e
        contenuti. Se qualcosa manca o è scritto male, correggilo nelle rispettive sezioni.
      </p>

      {error && <div className="gcr-alert gcr-alert--error">{error}</div>}
      {copyMsg && <div className="gcr-alert gcr-alert--success">{copyMsg}</div>}

      <div className="bi-ai-context-grid">
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Contesto disponibile</h3>
          <p className="bi-overview-field">
            <span className="bi-overview-field__label">Fonte</span>
            {context.primarySource}
          </p>
          {included.length > 0 ? (
            <ul className="bi-recommendations">
              {included.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          ) : (
            <p className="bi-panel__subtitle">Nessuna sezione compilata.</p>
          )}
        </section>

        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Sezioni mancanti</h3>
          {missing.length === 0 && emptySections.length === 0 ? (
            <p className="bi-panel__subtitle">Nessuna sezione critica mancante.</p>
          ) : (
            <ul className="bi-recommendations">
              {missing.map((m) => (
                <li key={m}>{m}</li>
              ))}
              {emptySections.map((s) => (
                <li key={`empty-${s}`}>{s}: non compilata</li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="bi-profile-block gcr-card" style={{ marginTop: "1rem" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "0.75rem",
          }}
        >
          <h3 className="bi-panel__title" style={{ margin: 0 }}>
            AI Context Preview
          </h3>
          <div className="bi-profile-block__actions" style={{ margin: 0 }}>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              disabled={isFetching}
              onClick={() => refetch()}
            >
              {isFetching ? "Aggiornamento…" : "Aggiorna anteprima"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={!previewText}
              onClick={handleCopy}
            >
              Copia contesto
            </button>
          </div>
        </div>
        <pre className="bi-ai-context-preview">{previewText || "Nessun testo disponibile."}</pre>
      </section>
    </div>
  );
}
