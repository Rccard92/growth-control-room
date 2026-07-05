import { useEffect, useState } from "react";
import {
  useSearchConsoleSites,
  useSelectSearchConsoleSite,
} from "../../hooks/useGoogleIntegrations";

interface GoogleSearchConsolePropertyPanelProps {
  projectId: string;
  selectedSiteUrl?: string | null;
}

export function GoogleSearchConsolePropertyPanel({
  projectId,
  selectedSiteUrl,
}: GoogleSearchConsolePropertyPanelProps) {
  const [isEditing, setIsEditing] = useState(!selectedSiteUrl);
  const [selectedUrl, setSelectedUrl] = useState(selectedSiteUrl ?? "");
  const [feedback, setFeedback] = useState<string | null>(null);

  const sitesQuery = useSearchConsoleSites(projectId, isEditing);
  const selectSite = useSelectSearchConsoleSite(projectId);

  useEffect(() => {
    setSelectedUrl(selectedSiteUrl ?? "");
    setIsEditing(!selectedSiteUrl);
  }, [selectedSiteUrl]);

  async function handleSave() {
    if (!selectedUrl) return;
    setFeedback(null);
    try {
      const response = await selectSite.mutateAsync({ siteUrl: selectedUrl });
      setFeedback(response.message);
      setIsEditing(false);
    } catch (error) {
      setFeedback(
        error instanceof Error ? error.message : "Impossibile salvare la proprietà Search Console.",
      );
    }
  }

  if (!isEditing && selectedSiteUrl) {
    return (
      <div className="gsc-property-panel gcr-card">
        <p className="gsc-property-panel__current">
          Proprietà: <strong>{selectedSiteUrl}</strong>
        </p>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary gcr-btn--sm"
          onClick={() => setIsEditing(true)}
        >
          Cambia proprietà
        </button>
      </div>
    );
  }

  return (
    <div className="gsc-property-panel gcr-card">
      <p className="gsc-property-panel__hint">
        Seleziona la proprietà Search Console da usare nel Growth Audit.
      </p>
      {sitesQuery.isLoading ? (
        <p>Caricamento proprietà…</p>
      ) : sitesQuery.isError ? (
        <p className="gcr-alert gcr-alert--error">
          Impossibile caricare le proprietà Search Console.
        </p>
      ) : (
        <label className="gsc-property-panel__field">
          <span>Proprietà</span>
          <select
            value={selectedUrl}
            onChange={(event) => setSelectedUrl(event.target.value)}
            disabled={selectSite.isPending}
          >
            <option value="">Seleziona una proprietà</option>
            {(sitesQuery.data?.sites ?? []).map((site) => (
              <option key={site.siteUrl} value={site.siteUrl}>
                {site.siteUrl}
                {site.permissionLevel ? ` (${site.permissionLevel})` : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="gsc-property-panel__actions">
        <button
          type="button"
          className="gcr-btn gcr-btn--primary gcr-btn--sm"
          disabled={!selectedUrl || selectSite.isPending}
          onClick={() => void handleSave()}
        >
          {selectSite.isPending ? "Salvataggio…" : "Salva proprietà"}
        </button>
        {selectedSiteUrl && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => {
              setIsEditing(false);
              setSelectedUrl(selectedSiteUrl);
            }}
          >
            Annulla
          </button>
        )}
      </div>
      {feedback && <p className="gsc-property-panel__feedback">{feedback}</p>}
    </div>
  );
}
