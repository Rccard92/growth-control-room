import { useState } from "react";
import { EditorialCalendar } from "./EditorialCalendar";
import { EditorialItemModal } from "./EditorialItemModal";
import { EditorialPlanWizard } from "./EditorialPlanWizard";
import { EditorialBatchBriefModal } from "./EditorialBatchBriefModal";
import { hasEditorialBrief } from "./editorial-brief-utils";
import {
  useEditorialItems,
  useStartEditorialBriefBatch,
} from "../../../hooks/useContentSeoEditorial";
import type { ContentSeoEditorialItem } from "@gcr/shared";

function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

interface ContentSeoEditorialRoomProps {
  projectId: string;
  shopifyConnected: boolean;
}

export function ContentSeoEditorialRoom({
  projectId,
  shopifyConnected,
}: ContentSeoEditorialRoomProps) {
  const [month, setMonth] = useState(currentMonth);
  const [selectedItem, setSelectedItem] = useState<ContentSeoEditorialItem | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchJobId, setBatchJobId] = useState<string | null>(null);
  const [batchAlert, setBatchAlert] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useEditorialItems(projectId, month);
  const allItemsQuery = useEditorialItems(projectId);
  const batchMutation = useStartEditorialBriefBatch(projectId);
  const items = data?.items ?? [];
  const allItems = allItemsQuery.data?.items ?? [];

  const ideaWithoutBriefCount = items.filter(
    (i) => i.status === "idea" && !hasEditorialBrief(i.briefPayload),
  ).length;

  async function handleStartBatch() {
    setBatchAlert(null);
    if (ideaWithoutBriefCount === 0) {
      setBatchAlert("Nessun contenuto in stato Idea da elaborare.");
      return;
    }
    try {
      const job = await batchMutation.mutateAsync({ month, onlyStatus: "idea" });
      setBatchJobId(job.jobId);
      setBatchModalOpen(true);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "";
      if (msg.includes("AI non configurata")) {
        setBatchAlert("AI non configurata. Inserisci OPENAI_API_KEY per generare i brief.");
      } else if (msg.includes("Nessun contenuto")) {
        setBatchAlert("Nessun contenuto in stato Idea da elaborare.");
      } else {
        setBatchAlert("Impossibile avviare la generazione massiva. Riprova più tardi.");
      }
    }
  }

  return (
    <div className="editorial-room">
      <div className="editorial-room__toolbar">
        <div>
          <h2 className="editorial-room__title">Calendario editoriale</h2>
          <p className="editorial-room__subtitle">
            Pianifica articoli blog e ricette, genera brief SEO con Brand Intelligence e approva prima della scrittura.
          </p>
        </div>
        <div className="editorial-room__toolbar-actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={batchMutation.isPending}
            onClick={() => void handleStartBatch()}
          >
            {batchMutation.isPending ? "Avvio…" : "Genera tutti i brief"}
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={() => setWizardOpen(true)}
          >
            Crea piano editoriale
          </button>
        </div>
      </div>

      {batchAlert && (
        <div className="gcr-alert gcr-alert--warning">{batchAlert}</div>
      )}

      {isError && (
        <div className="gcr-alert gcr-alert--error">
          {error instanceof Error ? error.message : "Impossibile caricare il calendario."}
        </div>
      )}

      {isLoading ? (
        <div className="gcr-skeleton editorial-calendar-skeleton" />
      ) : items.length === 0 ? (
        <div className="gcr-card content-seo-empty">
          <h3 className="gcr-card__title">Nessun contenuto pianificato</h3>
          <p className="gcr-card__description">
            Crea un piano editoriale per popolare il calendario con idee, guide e ricette.
          </p>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary gcr-btn--sm"
            onClick={() => setWizardOpen(true)}
          >
            Crea piano editoriale
          </button>
        </div>
      ) : (
        <EditorialCalendar
          month={month}
          items={items}
          onMonthChange={setMonth}
          onItemClick={setSelectedItem}
        />
      )}

      <EditorialItemModal
        open={Boolean(selectedItem)}
        item={selectedItem}
        projectId={projectId}
        allItems={allItems}
        onClose={() => setSelectedItem(null)}
        onItemUpdated={(updated) => {
          setSelectedItem(updated);
          void refetch();
          void allItemsQuery.refetch();
        }}
      />

      <EditorialPlanWizard
        open={wizardOpen}
        projectId={projectId}
        shopifyConnected={shopifyConnected}
        onClose={() => setWizardOpen(false)}
        onConfirmed={() => void refetch()}
      />

      <EditorialBatchBriefModal
        open={batchModalOpen}
        projectId={projectId}
        jobId={batchJobId}
        onClose={() => setBatchModalOpen(false)}
        onComplete={() => {
          void refetch();
          void allItemsQuery.refetch();
        }}
      />
    </div>
  );
}
