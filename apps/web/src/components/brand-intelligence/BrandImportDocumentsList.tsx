import type { BrandSourceDocument } from "@gcr/shared";

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Caricato",
  extracting: "Estrazione AI…",
  extracted: "Estratto",
  failed: "Errore",
  reviewed: "Revisionato",
};

interface BrandImportDocumentsListProps {
  documents: Pick<
    BrandSourceDocument,
    "id" | "filename" | "extractionStatus" | "extractionError" | "documentType" | "documentSummary" | "fileSize" | "progressPercent" | "currentStep"
  >[];
}

export function BrandImportDocumentsList({ documents }: BrandImportDocumentsListProps) {
  if (documents.length === 0) {
    return <p className="bi-panel__subtitle">Nessun documento caricato.</p>;
  }

  return (
    <div className="bi-list">
      {documents.map((doc) => (
        <div key={doc.id} className="bi-list__item">
          <div>
            <div className="bi-list__item-title">{doc.filename}</div>
            <div className="bi-list__item-meta">
              {doc.fileSize != null ? `${(doc.fileSize / 1024).toFixed(0)} KB · ` : ""}
              {STATUS_LABELS[doc.extractionStatus] ?? doc.extractionStatus}
              {doc.progressPercent != null && doc.progressPercent > 0 && doc.progressPercent < 100
                ? ` · ${doc.progressPercent}%`
                : ""}
              {doc.currentStep ? ` · ${doc.currentStep}` : ""}
              {doc.documentType ? ` · ${doc.documentType}` : ""}
            </div>
            {doc.extractionError && (
              <div className="bi-list__item-meta" style={{ color: "#fb7185" }}>
                {doc.extractionError}
              </div>
            )}
            {doc.documentSummary && (
              <div className="bi-list__item-meta">{doc.documentSummary.slice(0, 160)}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
