import { BrandImportDocumentsList } from "./BrandImportDocumentsList";
import { useBrandSourceDocuments } from "../../hooks/useBrandIntelligence";

interface BrandSourcesPanelProps {
  projectId: string;
  onGoToImport: () => void;
}

export function BrandSourcesPanel({ projectId, onGoToImport }: BrandSourcesPanelProps) {
  const { data: documents = [], isLoading } = useBrandSourceDocuments(projectId);

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Documenti caricati</h3>
      <p className="bi-panel__subtitle">
        Elenco dei file importati. Per caricare nuovi documenti o revisionare le estrazioni AI, usa Import AI.
      </p>
      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : documents.length === 0 ? (
        <div className="bi-coming-soon">
          <p>Nessun documento ancora.</p>
          <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={onGoToImport}>
            Carica documenti
          </button>
        </div>
      ) : (
        <>
          <BrandImportDocumentsList documents={documents} />
          <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={onGoToImport}>
            Vai a Import AI
          </button>
        </>
      )}
    </div>
  );
}
