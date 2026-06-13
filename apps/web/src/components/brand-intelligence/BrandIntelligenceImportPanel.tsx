import { useCallback, useState } from "react";
import type { BrandExternalSourceInput } from "@gcr/shared";
import { BrandAnalyzedSourcesPanel } from "./BrandAnalyzedSourcesPanel";
import { BrandExtractedFactsReview } from "./BrandExtractedFactsReview";
import { BrandExternalSourcesForm } from "./BrandExternalSourcesForm";
import { BrandFileDropzone } from "./BrandFileDropzone";
import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import { BrandImportHistoryPanel } from "./BrandImportHistoryPanel";
import { BrandImportProgressBar } from "./BrandImportProgressBar";
import { BrandSectionDraftsGrid } from "./BrandSectionDraftsGrid";
import {
  useBrandExtractedFacts,
  useBrandProfile,
  useBrandSourceDocuments,
  useImportBatchStatus,
  useImportBatches,
  useSectionDrafts,
  useSynthesizeImportBatch,
  useStartImportBatch,
  useUploadBrandSources,
} from "../../hooks/useBrandIntelligence";

const STEPS = [
  { id: 1, label: "Fonti e documenti" },
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
  const [brandName, setBrandName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [externalSources, setExternalSources] = useState<BrandExternalSourceInput[]>([]);

  const { data: profile } = useBrandProfile(projectId);
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

  const handleFormChange = useCallback(
    (
      values: { brandName: string; websiteUrl: string },
      sources: BrandExternalSourceInput[],
    ) => {
      setBrandName(values.brandName);
      setWebsiteUrl(values.websiteUrl);
      setExternalSources(sources);
    },
    [],
  );

  async function startImport(files: File[]) {
    setUploadError(null);
    const hasBrand = Boolean(brandName.trim());
    const hasWebsite = Boolean(websiteUrl.trim());
    const hasFiles = files.length > 0;

    if (!hasBrand && !hasWebsite && !hasFiles && externalSources.length === 0) {
      setUploadError("Inserisci almeno il nome brand, il sito web o un file da caricare.");
      return;
    }

    try {
      const result = await upload.mutateAsync({
        files,
        brandName: brandName.trim() || undefined,
        websiteUrl: websiteUrl.trim() || undefined,
        sources: externalSources.length ? externalSources : undefined,
        batchName: brandName.trim() || undefined,
      });
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

  const analyzedSources = batchStatus?.externalSources ?? [];

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
          <BrandExternalSourcesForm
            initialBrandName={profile?.brandName ?? ""}
            initialWebsiteUrl={profile?.websiteUrl ?? ""}
            onChange={handleFormChange}
          />

          <h3 className="bi-panel__title" style={{ marginTop: "1.5rem" }}>
            Carica documenti
          </h3>
          <p className="bi-panel__subtitle">
            PDF, Word, cataloghi o schede prodotto. L&apos;AI arricchirà le bozze anche con le fonti
            brand indicate sopra. Nessun dato ufficiale viene sovrascritto automaticamente.
          </p>
          <BrandFileDropzone
            onFilesSelected={startImport}
            disabled={upload.isPending || startBatch.isPending}
          />
          <div className="bi-wizard__actions" style={{ marginTop: "0.75rem" }}>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              disabled={upload.isPending || startBatch.isPending}
              onClick={() => startImport([])}
            >
              Avvia solo con fonti brand (senza file)
            </button>
          </div>
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
            Estrazione testo, recupero fonti esterne, facts, sintesi per sezione e rilevamento
            conflitti. Il progresso si aggiorna automaticamente ogni 2 secondi.
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
              <BrandAnalyzedSourcesPanel
                sources={analyzedSources}
                warnings={batchStatus.warnings}
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
            nella Brand Intelligence ufficiale. I facts e le fonti esterne restano come evidenze.
          </p>

          {analyzedSources.length > 0 && (
            <BrandAnalyzedSourcesPanel sources={analyzedSources} warnings={batchStatus?.warnings} />
          )}

          {batchId && (
            <div className="bi-wizard__actions" style={{ marginBottom: "1rem" }}>
              <button
                type="button"
                className="gcr-btn gcr-btn--primary gcr-btn--sm"
                disabled={synthesize.isPending}
                onClick={() => synthesize.mutate(batchId)}
              >
                {synthesize.isPending
                  ? "Rigenerazione in corso…"
                  : "Rigenera bozze usando file + fonti esterne"}
              </button>
            </div>
          )}

          <BrandSectionDraftsGrid
            projectId={projectId}
            batchId={batchId}
            drafts={sectionDrafts}
            externalSources={analyzedSources}
          />

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
