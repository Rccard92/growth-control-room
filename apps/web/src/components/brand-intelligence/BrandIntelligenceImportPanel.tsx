import { useState } from "react";
import type { BrandApplyFactsResponse } from "@gcr/shared";
import { BrandExtractedFactsReview, BrandImportApplySummary } from "./BrandExtractedFactsReview";
import { BrandFileDropzone } from "./BrandFileDropzone";
import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import { BrandImportHistoryPanel } from "./BrandImportHistoryPanel";
import { BrandImportProgressBar } from "./BrandImportProgressBar";
import {
  useApplyBrandExtractedFacts,
  useBrandExtractedFacts,
  useBrandSourceDocuments,
  useImportBatchStatus,
  useImportBatches,
  usePatchBrandExtractedFact,
  useStartImportBatch,
  useUploadBrandSources,
} from "../../hooks/useBrandIntelligence";

const STEPS = [
  { id: 1, label: "Carica documenti" },
  { id: 2, label: "Elaborazione" },
  { id: 3, label: "Revisiona e approva" },
] as const;

const READY_STATUSES = new Set(["review_ready", "partially_failed", "completed"]);

interface BrandIntelligenceImportPanelProps {
  projectId: string;
}

export function BrandIntelligenceImportPanel({ projectId }: BrandIntelligenceImportPanelProps) {
  const [step, setStep] = useState(1);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [applyResult, setApplyResult] = useState<BrandApplyFactsResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: documents = [] } = useBrandSourceDocuments(projectId);
  const { data: batches = [] } = useImportBatches(projectId);
  const { data: batchStatus } = useImportBatchStatus(projectId, batchId ?? undefined, {
    enabled: Boolean(batchId),
    polling: step === 2,
  });
  const { data: facts = [] } = useBrandExtractedFacts(projectId, batchId ? { batchId } : undefined);

  const upload = useUploadBrandSources(projectId);
  const startBatch = useStartImportBatch(projectId);
  const patchFact = usePatchBrandExtractedFact(projectId);
  const applyFacts = useApplyBrandExtractedFacts(projectId);

  const isProcessing = Boolean(
    batchStatus &&
      !READY_STATUSES.has(batchStatus.status) &&
      batchStatus.status !== "failed",
  );

  async function handleUpload(files: File[]) {
    setUploadError(null);
    setApplyResult(null);
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
    setApplyResult(null);
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
            Nessun dato ufficiale viene sovrascritto automaticamente.
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
            Estrazione testo, analisi AI e rilevamento conflitti con i dati ufficiali esistenti.
            Puoi lasciare questa pagina aperta: il progresso si aggiorna automaticamente.
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
                    Revisiona informazioni estratte ({batchStatus.needsReviewFacts + batchStatus.approvedFacts})
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
          <h3 className="bi-panel__title">Revisiona e approva</h3>
          <p className="bi-panel__subtitle">
            Approva, modifica o rifiuta ogni informazione. I conflitti con dati esistenti sono evidenziati.
            Solo i facts approvati verranno salvati nella Brand Intelligence ufficiale.
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
              const result = await applyFacts.mutateAsync({ factIds: ids, batchId: batchId ?? undefined });
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

      <BrandImportHistoryPanel
        projectId={projectId}
        batches={batches}
        onOpenReview={openReviewForBatch}
      />
    </div>
  );
}
