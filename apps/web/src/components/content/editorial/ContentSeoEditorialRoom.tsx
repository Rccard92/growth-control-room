import { useState } from "react";
import { EditorialCalendar } from "./EditorialCalendar";
import { EditorialItemDrawer } from "./EditorialItemDrawer";
import { EditorialPlanWizard } from "./EditorialPlanWizard";
import { EditorialStatusLegend } from "./EditorialStatusLegend";
import { useEditorialItems } from "../../../hooks/useContentSeoEditorial";
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

  const { data, isLoading, isError, error, refetch } = useEditorialItems(projectId, month);
  const items = data?.items ?? [];

  return (
    <div className="editorial-room">
      <div className="editorial-room__toolbar">
        <div>
          <h2 className="editorial-room__title">Calendario editoriale</h2>
          <p className="editorial-room__subtitle">
            Pianifica articoli blog e ricette. La generazione brief e pubblicazione Shopify arriveranno nei prossimi step.
          </p>
        </div>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          onClick={() => setWizardOpen(true)}
        >
          Crea piano editoriale
        </button>
      </div>

      <EditorialStatusLegend />

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

      <EditorialItemDrawer
        open={Boolean(selectedItem)}
        item={selectedItem}
        projectId={projectId}
        onClose={() => setSelectedItem(null)}
      />

      <EditorialPlanWizard
        open={wizardOpen}
        projectId={projectId}
        shopifyConnected={shopifyConnected}
        onClose={() => setWizardOpen(false)}
        onConfirmed={() => void refetch()}
      />
    </div>
  );
}
