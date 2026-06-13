import { useState } from "react";
import type { BrandApplyFactsResponse } from "@gcr/shared";
import { BrandExtractedFactsReview, BrandImportApplySummary } from "./BrandExtractedFactsReview";
import { BrandFileDropzone } from "./BrandFileDropzone";
import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import {
  useApplyBrandExtractedFacts,
  useBrandExtractedFacts,
  useBrandSourceDocuments,
  useExtractBrandSourcesBatch,
  usePatchBrandExtractedFact,
  useUploadBrandSources,
} from "../../hooks/useBrandIntelligence";

const STEPS = [
  { id: 1, label: "Carica documenti" },
  { id: 2, label: "Estrai con AI" },
  { id: 3, label: "Revisiona e approva" },
] as const;

interface BrandIntelligenceImportPanelProps {
  projectId: string;
}

export function BrandIntelligenceImportPanel({ projectId }: BrandIntelligenceImportPanelProps) {
  const [step, setStep] = useState(1);
  const [applyResult, setApplyResult] = useState<BrandApplyFactsResponse | null>(null);
  const [extractError, setExtractError] = useState<string | null>(null);

  const { data: documents = [] } = useBrandSourceDocuments(projectId);
  const { data: facts = [] } = useBrandExtractedFacts(projectId);
  const upload = useUploadBrandSources(projectId);
  const extractBatch = useExtractBrandSourcesBatch(projectId);
  const patchFact = usePatchBrandExtractedFact(projectId);
  const applyFacts = useApplyBrandExtractedFacts(projectId);

  const uploadableDocs = documents.filter(
    (d) => d.extractionStatus === "uploaded" && !d.extractionError,
  );
  const isExtracting = documents.some((d) => d.extractionStatus === "extracting");

  async function handleUpload(files: File[]) {
    await upload.mutateAsync(files);
    setStep(2);
  }

  async function handleExtract() {
    setExtractError(null);
    const ids = uploadableDocs.map((d) => d.id);
    if (ids.length === 0) {
      const extractedIds = documents
        .filter((d) => d.extractionStatus === "extracted")
        .map((d) => d.id);
      if (extractedIds.length) {
        setStep(3);
        return;
      }
      setExtractError("Nessun documento pronto per l'estrazione. Carica file validi prima.");
      return;
    }
    try {
      const result = await extractBatch.mutateAsync(ids);
      const failed = result.results.filter((r) => r.status === "failed");
      if (failed.length === result.results.length) {
        setExtractError(failed[0]?.error ?? "Estrazione AI non riuscita.");
      } else {
        setStep(3);
      }
    } catch (e) {
      setExtractError(e instanceof Error ? e.message : "Estrazione AI non riuscita.");
    }
  }

  return (
    <div className="bi-import">
      <div className="bi-wizard__stepper">
        {STEPS.map((s) => (
          <div
            key={s.id}
            className={`bi-wizard__step ${step === s.id ? "bi-wizard__step--active" : ""} ${step > s.id ? "bi-wizard__step--done" : ""}`}
          >
            <span className="bi-wizard__dot">{step > s.id ? "✓" : s.id}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="bi-panel">
          <h3 className="bi-panel__title">Carica documenti</h3>
          <p className="bi-panel__subtitle">
            PDF, Word, cataloghi o schede prodotto. L&apos;AI estrarrà informazioni da revisionare prima del salvataggio.
          </p>
          <BrandFileDropzone onFilesSelected={handleUpload} disabled={upload.isPending} />
          {upload.isPending && <p className="bi-panel__subtitle">Caricamento…</p>}
          <BrandImportDocumentsList documents={documents} />
        </div>
      )}

      {step === 2 && (
        <div className="bi-panel">
          <h3 className="bi-panel__title">Estrai con AI</h3>
          <p className="bi-panel__subtitle">
            Analizza il testo estratto e genera proposte organizzate per sezione. Nessun salvataggio automatico.
          </p>
          <BrandImportDocumentsList documents={documents} />
          {extractError && (
            <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
              {extractError}
              {extractError.includes("OPENAI") && (
                <span> Upload ed estrazione testo restano disponibili senza OpenAI.</span>
              )}
            </div>
          )}
          <div className="bi-wizard__actions">
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(1)}>
              Indietro
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={extractBatch.isPending || isExtracting}
              onClick={handleExtract}
            >
              {extractBatch.isPending || isExtracting ? "Estrazione…" : "Estrai informazioni"}
            </button>
            {documents.some((d) => d.extractionStatus === "extracted") && (
              <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(3)}>
                Vai alla revisione
              </button>
            )}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bi-panel">
          <h3 className="bi-panel__title">Revisiona e approva</h3>
          <p className="bi-panel__subtitle">
            Approva, modifica o rifiuta ogni informazione. Solo i facts approvati verranno salvati nella Brand Intelligence ufficiale.
          </p>
          <BrandExtractedFactsReview
            facts={facts.filter((f) => f.status !== "rejected")}
            onApprove={(id) => patchFact.mutate({ factId: id, data: { status: "approved" } })}
            onReject={(id) => patchFact.mutate({ factId: id, data: { status: "rejected" } })}
            onMoveSection={(id, section) =>
              patchFact.mutate({ factId: id, data: { targetSection: section } })
            }
            onEditValue={(id, value) =>
              patchFact.mutate({ factId: id, data: { extractedValue: value } })
            }
            onApply={async (ids) => {
              const result = await applyFacts.mutateAsync(ids);
              setApplyResult(result);
            }}
            applying={applyFacts.isPending}
          />
          {applyResult && <BrandImportApplySummary result={applyResult} />}
          <div className="bi-wizard__actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(2)}>
              Indietro
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
