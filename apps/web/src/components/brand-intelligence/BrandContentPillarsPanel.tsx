import { FormEvent, useState } from "react";
import { useBrandPillars, useCreateBrandPillar } from "../../hooks/useBrandIntelligence";

interface BrandContentPillarsPanelProps {
  projectId: string;
}

export function BrandContentPillarsPanel({ projectId }: BrandContentPillarsPanelProps) {
  const { data: items = [], isLoading } = useBrandPillars(projectId);
  const create = useCreateBrandPillar(projectId);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), description: description.trim() || undefined },
      { onSuccess: () => { setName(""); setDescription(""); } },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Content Pillars</h3>
      <p className="bi-panel__subtitle">Pilastri editoriali e temi ricorrenti del brand.</p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessun pillar ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.name}</div>
                {item.description && <div className="bi-list__item-meta">{item.description}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="pillarName">Nome *</label>
            <input id="pillarName" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="pillarDesc">Descrizione</label>
            <textarea
              id="pillarDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi pillar"}
          </button>
        </div>
      </form>
    </div>
  );
}
