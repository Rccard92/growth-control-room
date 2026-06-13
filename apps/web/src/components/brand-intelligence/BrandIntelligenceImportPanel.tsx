import { useCallback, useEffect, useState } from "react";
import type { BrandExternalSourceInput } from "@gcr/shared";
import { BrandAnalyzedSourcesPanel } from "./BrandAnalyzedSourcesPanel";
import { BrandExtractedFactsReview } from "./BrandExtractedFactsReview";
import { BrandExternalSourcesForm } from "./BrandExternalSourcesForm";
import { BrandFileDropzone } from "./BrandFileDropzone";
import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import { BrandImportHistoryPanel } from "./BrandImportHistoryPanel";
import { BrandImportProgressBar } from "./BrandImportProgressBar";
import { BrandIntelligenceBriefPanel } from "./BrandIntelligenceBriefPanel";
import { BrandSectionDraftsGrid } from "./BrandSectionDraftsGrid";
import {
  useBrandBrief,
  useBrandExtractedFacts,
  useBrandProfile,
  useBrandSourceDocuments,
  useCreateImportBatch,
  useImportBatchStatus,
  useImportBatches,
  useRefreshBatchContext,
  useSaveBatchSources,
  useSectionDrafts,
  useStartImportBatch,
  useUploadBrandSources,
} from "../../hooks/useBrandIntelligence";

const STEPS = [
  { id: 1, label: "Fonti e documenti" },
  { id: 2, label: "Elaborazione" },
  { id: 3, label: "Brand Brief" },
] as const;

const READY_STATUSES = new Set(["review_ready", "partially_failed", "completed"]);

interface BrandIntelligenceImportPanelProps {
  projectId: string;
}

export function BrandIntelligenceImportPanel({ projectId }: BrandIntelligenceImportPanelProps) {
  const [step, setStep] = useState(1);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [briefId, setBriefId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [brandName, setBrandName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [externalSources, setExternalSources] = useState<BrandExternalSourceInput[]>([]);

  const { data: profile } = useBrandProfile(projectId);
  const { data: documents = [] } = useBrandSourceDocuments(projectId);
  const { data: batches = [] } = useImportBatches(projectId);
  const { data: batchStatus } = useImportBatchStatus(projectId, batchId ?? undefined, {
    enabled: Boolean(batchId),
    polling: step === 2 || isRefreshing,
  });
  const { data: sectionDrafts = [] } = useSectionDrafts(projectId, batchId ? { batchId } : undefined);
  const { data: facts = [] } = useBrandExtractedFacts(projectId, batchId ? { batchId } : undefined);
  const { data: brief, isError: briefLoadFailed } = useBrandBrief(projectId, briefId ?? undefined);

  const upload = useUploadBrandSources(projectId);
  const startBatch = useStartImportBatch(projectId);
  const createBatch = useCreateImportBatch(projectId);
  const saveSources = useSaveBatchSources(projectId);
  const refreshContext = useRefreshBatchContext(projectId);

  const isProcessing = Boolean(
    batchStatus &&
      !READY_STATUSES.has(batchStatus.status) &&
      batchStatus.status !== "failed",
  );

  const batchFileCount = batchStatus?.documents?.length ?? 0;
  const canRegenerate = Boolean(
    brandName.trim() ||
      websiteUrl.trim() ||
      externalSources.length > 0 ||
      batchFileCount > 0,
  );

  const handleFormChange = useCallback(
    (
      values: { brandName: string; websiteUrl: string },
      sources: BrandExternalSourceInput[],
    ) => {
      setBrandName(values.brandName);
      setWebsiteUrl(values.websiteUrl);
      setExternalSources(sources);
      setSaveSuccess(null);
    },
    [],
  );

  useEffect(() => {
    if (!isRefreshing || !batchStatus) return;
    if (READY_STATUSES.has(batchStatus.status)) {
      setIsRefreshing(false);
      setStep(3);
    }
  }, [batchStatus, isRefreshing]);

  async function ensureBatch(): Promise<string> {
    if (batchId) return batchId;
    const result = await createBatch.mutateAsync({
      brandName: brandName.trim() || undefined,
      websiteUrl: websiteUrl.trim() || undefined,
      sources: externalSources.length ? externalSources : undefined,
      batchName: brandName.trim() || undefined,
    });
    setBatchId(result.batchId);
    return result.batchId;
  }

  async function handleSaveSources() {
    setSourcesError(null);
    setSaveSuccess(null);
    try {
      const id = await ensureBatch();
      const result = await saveSources.mutateAsync({
        batchId: id,
        body: {
          brandName: brandName.trim() || undefined,
          websiteUrl: websiteUrl.trim() || undefined,
          sources: externalSources,
        },
      });
      setSaveSuccess(result.message || "Fonti brand salvate.");
    } catch (e) {
      setSourcesError(e instanceof Error ? e.message : "Salvataggio fonti non riuscito.");
    }
  }

  async function handleRefreshAndRegenerate() {
    setSourcesError(null);
    setSaveSuccess(null);

    if (!canRegenerate) {
      setSourcesError(
        "Inserisci almeno il nome brand, il sito web, una fonte esterna o carica file nel batch.",
      );
      return;
    }

    try {
      const id = await ensureBatch();
      await saveSources.mutateAsync({
        batchId: id,
        body: {
          brandName: brandName.trim() || undefined,
          websiteUrl: websiteUrl.trim() || undefined,
          sources: externalSources,
        },
      });
      setIsRefreshing(true);
      setStep(2);
      await refreshContext.mutateAsync({ batchId: id });
    } catch (e) {
      setIsRefreshing(false);
      setSourcesError(e instanceof Error ? e.message : "Rigenerazione non riuscita.");
    }
  }

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
        batchId: batchId ?? undefined,
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
    setBriefId(null);
    setStep(3);
  }

  const analyzedSources = batchStatus?.externalSources ?? [];
  const sourcesBusy = saveSources.isPending || refreshContext.isPending || createBatch.isPending;

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
            hydrateFromBatch={
              batchId && batchStatus
                ? {
                    brandName: batchStatus.declaredBrandName,
                    websiteUrl: batchStatus.declaredWebsiteUrl,
                    sources: analyzedSources,
                  }
                : undefined
            }
            onChange={handleFormChange}
          >
            <div className="bi-sources-actions">
              <button
                type="button"
                className="gcr-btn gcr-btn--ghost"
                disabled={sourcesBusy}
                onClick={() => void handleSaveSources()}
              >
                {saveSources.isPending ? "Salvataggio…" : "Salva fonti brand"}
              </button>
              <button
                type="button"
                className="gcr-btn gcr-btn--primary bi-sources-actions__primary"
                disabled={sourcesBusy || !canRegenerate}
                onClick={() => void handleRefreshAndRegenerate()}
              >
                {refreshContext.isPending || isRefreshing
                  ? "Rigenerazione in corso…"
                  : "Aggiorna fonti e rigenera Brand Intelligence"}
              </button>
            </div>
            {saveSuccess && <p className="bi-sources-save-success">{saveSuccess}</p>}
            <p className="bi-sources-actions__hint">
              Le fonti verranno usate per rigenerare bozze più complete a partire da sito, social e
              recensioni pubbliche.
            </p>
            <p className="bi-sources-actions__hint">
              Verranno generate nuove bozze da revisionare. I dati ufficiali già approvati non
              saranno sovrascritti automaticamente.
            </p>
            <p className="bi-sources-actions__hint">
              Puoi generare una prima Brand Intelligence anche solo da sito e fonti pubbliche, senza
              caricare file.
            </p>
            {sourcesError && (
              <div className="gcr-alert gcr-alert--error" style={{ marginTop: "0.75rem" }}>
                {sourcesError}
              </div>
            )}
          </BrandExternalSourcesForm>

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
            Estrazione testo, recupero fonti esterne e facts. Al termine genera il Brand Intelligence
            Brief. Il progresso si aggiorna automaticamente ogni 2 secondi.
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
                    Genera Brand Intelligence Brief
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
              Modifica fonti
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bi-panel">
          <BrandIntelligenceBriefPanel
            projectId={projectId}
            batchId={batchId}
            brief={brief}
            briefLoadFailed={briefId ? briefLoadFailed : false}
            onBriefGenerated={setBriefId}
          />

          <div style={{ marginTop: "1.5rem" }}>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              onClick={() => setShowTechnicalDetails((v) => !v)}
            >
              {showTechnicalDetails
                ? "Nascondi dettagli tecnici"
                : "Dettagli tecnici — fonti e facts"}
            </button>
          </div>

          {showTechnicalDetails && (
            <div style={{ marginTop: "1rem" }}>
              {analyzedSources.length > 0 && (
                <BrandAnalyzedSourcesPanel
                  sources={analyzedSources}
                  warnings={batchStatus?.warnings}
                />
              )}
              <BrandSectionDraftsGrid
                projectId={projectId}
                batchId={batchId}
                drafts={sectionDrafts}
                externalSources={analyzedSources}
              />
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
            </div>
          )}

          <div className="bi-wizard__actions" style={{ marginTop: "1rem" }}>
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setStep(1)}>
              Aggiorna fonti e rigenera
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
