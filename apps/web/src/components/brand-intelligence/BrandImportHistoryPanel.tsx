import { useState } from "react";
import type { BrandImportBatchListItem, BrandImportBatchStatusResponse } from "@gcr/shared";
import { useImportBatchStatus } from "../../hooks/useBrandIntelligence";

interface BrandImportHistoryPanelProps {
  projectId: string;
  batches: BrandImportBatchListItem[];
  onOpenReview: (batchId: string) => void;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "In attesa",
    uploading: "Caricamento",
    extracting: "Estrazione",
    ai_processing: "Elaborazione AI",
    review_ready: "Pronto per revisione",
    partially_failed: "Parzialmente fallito",
    completed: "Completato",
    failed: "Fallito",
  };
  return map[status] ?? status;
}

function BatchLog({ status }: { status: BrandImportBatchStatusResponse }) {
  return (
    <div className="bi-batch-log">
      {status.currentStep && <p>Ultimo step: {status.currentStep}</p>}
      {status.errorMessage && <p className="bi-batch-log__error">{status.errorMessage}</p>}
      {status.warnings?.length > 0 && (
        <ul>
          {status.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
      {status.documents.map((doc) => (
        <div key={doc.id} className="bi-batch-log__doc">
          <strong>{doc.filename}</strong> — {doc.extractionStatus}
          {doc.currentStep && <span> · {doc.currentStep}</span>}
          {doc.extractionError && <span className="bi-batch-log__error"> · {doc.extractionError}</span>}
        </div>
      ))}
    </div>
  );
}

export function BrandImportHistoryPanel({
  projectId,
  batches,
  onOpenReview,
}: BrandImportHistoryPanelProps) {
  const [logBatchId, setLogBatchId] = useState<string | null>(null);
  const { data: logStatus } = useImportBatchStatus(projectId, logBatchId ?? undefined, {
    enabled: Boolean(logBatchId),
  });

  if (batches.length === 0) {
    return (
      <div className="bi-batch-history gcr-card">
        <h4 className="bi-panel__title">Storico import</h4>
        <p className="bi-panel__subtitle">Nessun import precedente. Il primo batch apparirà qui.</p>
      </div>
    );
  }

  return (
    <div className="bi-batch-history gcr-card">
      <h4 className="bi-panel__title">Storico import</h4>
      <p className="bi-panel__subtitle">
        Ogni import crea un nuovo batch. I dati approvati non vengono sovrascritti automaticamente.
      </p>
      <div className="bi-batch-history__list">
        {batches.map((batch) => (
          <div key={batch.id} className="bi-batch-history__item">
            <div className="bi-batch-history__main">
              <strong>{batch.name ?? `Import ${new Date(batch.createdAt).toLocaleDateString("it-IT")}`}</strong>
              <span className="bi-batch-history__status">{statusLabel(batch.status)}</span>
              <span className="bi-batch-history__meta">
                {batch.totalFiles} file · {batch.totalFacts} facts · {batch.needsReviewFacts} da revisionare
              </span>
            </div>
            <div className="bi-batch-history__actions">
              {(batch.status === "review_ready" ||
                batch.status === "partially_failed" ||
                batch.status === "completed") && (
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                  onClick={() => onOpenReview(batch.id)}
                >
                  Apri review
                </button>
              )}
              <button
                type="button"
                className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                onClick={() => setLogBatchId(logBatchId === batch.id ? null : batch.id)}
              >
                {logBatchId === batch.id ? "Nascondi log" : "Vedi log"}
              </button>
            </div>
            {logBatchId === batch.id && logStatus && <BatchLog status={logStatus} />}
          </div>
        ))}
      </div>
    </div>
  );
}
