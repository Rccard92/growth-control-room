import { FormEvent, useState } from "react";
import { useBrandAudience, useCreateBrandAudience } from "../../hooks/useBrandIntelligence";

interface BrandAudiencePanelProps {
  projectId: string;
}

export function BrandAudiencePanel({ projectId }: BrandAudiencePanelProps) {
  const { data: items = [], isLoading } = useBrandAudience(projectId);
  const create = useCreateBrandAudience(projectId);
  const [segmentName, setSegmentName] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!segmentName.trim()) return;
    create.mutate(
      { segmentName: segmentName.trim(), description: description.trim() || undefined },
      { onSuccess: () => { setSegmentName(""); setDescription(""); } },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Audience</h3>
      <p className="bi-panel__subtitle">Segmenti di pubblico, motivazioni e obiezioni.</p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessun segmento ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.segmentName}</div>
                {item.description && (
                  <div className="bi-list__item-meta">{item.description}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="segmentName">Nome segmento *</label>
            <input
              id="segmentName"
              value={segmentName}
              onChange={(e) => setSegmentName(e.target.value)}
              required
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="audienceDesc">Descrizione</label>
            <textarea
              id="audienceDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi segmento"}
          </button>
        </div>
      </form>
    </div>
  );
}
