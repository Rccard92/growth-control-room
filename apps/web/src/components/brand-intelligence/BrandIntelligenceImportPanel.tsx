import { useState } from "react";
import { BrandFileDropzone } from "./BrandFileDropzone";
import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import { BrandImportHistoryPanel } from "./BrandImportHistoryPanel";
import { BrandImportProgressBar } from "./BrandImportProgressBar";
import { BrandSectionDraftsGrid } from "./BrandSectionDraftsGrid";
import { BrandExtractedFactsReview } from "./BrandExtractedFactsReview";
import {
  useBrandExtractedFacts,
  useBrandSourceDocuments,
  useImportBatchStatus,
  useImportBatches,
  useSectionDrafts,
  useSynthesizeImportBatch,
  useStartImportBatch,
  useUploadBrandSources,
} from "../../hooks/useBrandIntelligence";

const STEPS = [
  { id: 1, label: "Carica documenti" },
  { id: 2, label: "Elaborazione" },
  { id: 3, label: "Revisiona bozze" },
] as const;

const READY_STATUSES = new Set(["review_ready", "partially_failed", "completed"]);

interface BrandIntelligenceImportPanelProps {
  projectId: string;
}

export function BrandIntelligenceImportPanel({ projectId }: BrandIntelligenceImportPanelProps) {
  const [step, setStep] = useState(1);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showDetailedFacts, setShowDetailedFacts] = useState(false);

  const { data: documents = [] } = useBrandSourceDocuments(projectId);
  const { data: batches = [] } = useImportBatches(projectId);
  const { data: batchStatus } = useImportBatchStatus(projectId, batchId ?? undefined, {
    enabled: Boolean(batchId),
    polling: step === 2,
  });
  const { data: sectionDrafts = [] } = useSectionDrafts(projectId, batchId ? { batchId } : undefined);
  const { data: facts = [] } = useBrandExtractedFacts(projectId, batchId ? { batchId } : undefined);

  const upload = useUploadBrandSources(projectId);
  const startBatch = useStartImportBatch(projectId);
  const synthesize = useSynthesizeImportBatch(projectId);

  const isProcessing = Boolean(
    batchStatus &&
      !READY_STATUSES.has(batchStatus.status) &&
      batchStatus.status !== "failed",
  );

  async function handleUpload(files: File[]) {
    setUploadError(null);
    try {
      const result = await upload.mutateAsync({ files });
      setBatchId(result.batchId);
      setStep(2);
      await startBatch.mutateAsync(result.batchId);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Caricamento non riuscito.");
    }
  }

  function openReviewForBatch(id: string) {
    setBatchId(id);
    setStep(3);
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
            PDF, Word, cataloghi o schede prodotto. L&apos;AI genererà bozze complete per sezione da
            revisionare prima del salvataggio. Nessun dato ufficiale viene sovrascritto automaticamente.
          </p>
          <BrandFileDropzone onFilesSelected={handleUpload} disabled={upload.isPending || startBatch.isPending} />
          {(upload.isPending || startBatch.isPending) && (
            <p className="bi-panel__subtitle">Caricamento e avvio elaborazione…</p>
          )}
          {uploadError && (
            <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
              {uploadError}
            </div>
          )}
          <BrandImportDocumentsList documents={documents.slice(0, 5)} />
        </div>
      )}

      {step === 2 && (
        <div className="bi-panel">
          <h3 className="bi-panel__title">Elaborazione import</h3>
          <p className="bi-panel__subtitle">
            Estrazione testo, facts, sintesi per sezione e rilevamento conflitti. Il progresso si
            aggiorna automaticamente ogni 2 secondi.
          </p>

          {batchStatus ? (
            <>
              <BrandImportProgressBar
                percent={batchStatus.progressPercent}
                currentStep={batchStatus.currentStep}
                processedFiles={batchStatus.processedFiles}
                totalFiles={batchStatus.totalFiles}
                totalFacts={batchStatus.totalFacts}
              />
              <BrandImportDocumentsList
                documents={batchStatus.documents.map((d) => ({
                  id: d.id,
                  filename: d.filename,
                  extractionStatus: d.extractionStatus,
                  progressPercent: d.progressPercent,
                  currentStep: d.currentStep,
                  extractionError: d.extractionError,
                }))}
              />
              {batchStatus.status === "failed" && (
                <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
                  {batchStatus.errorMessage ?? "Elaborazione fallita."}
                </div>
              )}
              {READY_STATUSES.has(batchStatus.status) && (
                <div className="bi-wizard__actions" style={{ marginTop: "1rem" }}>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--primary"
                    onClick={() => setStep(3)}
                  >
                    Revisiona bozze Brand Intelligence ({sectionDrafts.length || "…"} sezioni)
                  </button>
                </div>
              )}
              {isProcessing && (
                <p className="bi-panel__subtitle" style={{ marginTop: "1rem" }}>
                  Elaborazione in corso… aggiornamento ogni 2 secondi.
                </p>
              )}
            </>
          ) : (
            <p className="bi-panel__subtitle">In attesa dello stato batch…</p>
          )}

          <div className="bi-wizard__actions">
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(1)}>
              Nuovo upload
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bi-panel">
          <h3 className="bi-panel__title">Bozze Brand Intelligence generate</h3>
          <p className="bi-panel__subtitle">
            Revisiona ogni sezione come bozza completa. Approva e applica solo ciò che vuoi salvare
            nella Brand Intelligence ufficiale. I facts estratti restano disponibili come evidenze.
          </p>

          {batchId && sectionDrafts.length === 0 && (
            <div className="bi-wizard__actions" style={{ marginBottom: "1rem" }}>
              <button
                type="button"
                className="gcr-btn gcr-btn--primary gcr-btn--sm"
                disabled={synthesize.isPending}
                onClick={() => synthesize.mutate(batchId)}
              >
                {synthesize.isPending ? "Sintesi in corso…" : "Genera bozze sezione"}
              </button>
            </div>
          )}

          <BrandSectionDraftsGrid projectId={projectId} batchId={batchId} drafts={sectionDrafts} />

          <div style={{ marginTop: "1.5rem" }}>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              onClick={() => setShowDetailedFacts((v) => !v)}
            >
              {showDetailedFacts ? "Nascondi review dettagliata facts" : "Review dettagliata facts"}
            </button>
          </div>

          {showDetailedFacts && (
            <div style={{ marginTop: "1rem" }}>
              <BrandExtractedFactsReview
                facts={facts.filter((f) => f.status !== "rejected")}
                onApprove={() => {}}
                onReject={() => {}}
                onMoveSection={() => {}}
                onEditValue={() => {}}
                onApply={() => {}}
              />
            </div>
          )}

          <div className="bi-wizard__actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(2)}>
              Indietro
            </button>
          </div>
        </div>
      )}

      <BrandImportHistoryPanel
        projectId={projectId}
        batches={batches}
        onOpenReview={openReviewForBatch}
      />
    </div>
  );
}
