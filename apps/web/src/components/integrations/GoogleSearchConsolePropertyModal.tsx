import { useEffect, useState } from "react";
import { AppModal } from "../ui/AppModal";
import {
  useSearchConsoleSites,
  useSelectSearchConsoleSite,
} from "../../hooks/useGoogleIntegrations";

interface GoogleSearchConsolePropertyModalProps {
  projectId: string;
  selectedSiteUrl?: string | null;
  open: boolean;
  onClose: () => void;
}

export function GoogleSearchConsolePropertyModal({
  projectId,
  selectedSiteUrl,
  open,
  onClose,
}: GoogleSearchConsolePropertyModalProps) {
  const [selectedUrl, setSelectedUrl] = useState(selectedSiteUrl ?? "");
  const sitesQuery = useSearchConsoleSites(projectId, open);
  const selectSite = useSelectSearchConsoleSite(projectId);

  useEffect(() => {
    if (!open) return;
    setSelectedUrl(selectedSiteUrl ?? "");
  }, [open, selectedSiteUrl]);

  async function handleSave() {
    if (!selectedUrl) return;
    try {
      await selectSite.mutateAsync({ siteUrl: selectedUrl });
      onClose();
    } catch {
      // Error surfaced by mutation / global handlers; keep modal open.
    }
  }

  const sites = sitesQuery.data?.sites ?? [];

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Seleziona proprietà Search Console"
      subtitle="Scegli la proprietà da usare per arricchire Growth Audit con query, CTR, impression e posizione media."
      maxWidth="md"
      footer={
        <div className="gsc-property-modal__footer">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onClose}
            disabled={selectSite.isPending}
          >
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={!selectedUrl || selectSite.isPending}
            onClick={() => void handleSave()}
          >
            {selectSite.isPending ? "Salvataggio…" : "Salva proprietà"}
          </button>
        </div>
      }
    >
      {sitesQuery.isLoading ? (
        <p className="gsc-property-modal__status">Caricamento proprietà…</p>
      ) : sitesQuery.isError ? (
        <p className="gcr-alert gcr-alert--error">
          Impossibile caricare le proprietà Search Console.
        </p>
      ) : sites.length === 0 ? (
        <p className="gsc-property-modal__status">
          Nessuna proprietà Search Console trovata per questo account Google.
        </p>
      ) : (
        <div className="gsc-property-modal__list" role="listbox" aria-label="Proprietà Search Console">
          {sites.map((site) => {
            const isSelected = selectedUrl === site.siteUrl;
            return (
              <button
                key={site.siteUrl}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={`gsc-property-modal__option${isSelected ? " gsc-property-modal__option--selected" : ""}`}
                onClick={() => setSelectedUrl(site.siteUrl)}
              >
                <span className="gsc-property-modal__option-check" aria-hidden="true">
                  {isSelected ? "✓" : ""}
                </span>
                <span className="gsc-property-modal__option-body">
                  <span className="gsc-property-modal__option-main">{site.siteUrl}</span>
                  {site.permissionLevel && (
                    <span className="gsc-property-modal__permission">{site.permissionLevel}</span>
                  )}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </AppModal>
  );
}
