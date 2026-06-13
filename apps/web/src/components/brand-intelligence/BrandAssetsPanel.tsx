import { FormEvent, useState } from "react";
import { useBrandAssets, useCreateBrandAsset } from "../../hooks/useBrandIntelligence";

interface BrandAssetsPanelProps {
  projectId: string;
}

export function BrandAssetsPanel({ projectId }: BrandAssetsPanelProps) {
  const { data: items = [], isLoading } = useBrandAssets(projectId);
  const create = useCreateBrandAsset(projectId);
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState<"logo" | "color" | "font" | "image" | "other">("logo");
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), assetType, value: value.trim() || undefined },
      { onSuccess: () => { setName(""); setValue(""); } },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Assets</h3>
      <p className="bi-panel__subtitle">
        Logo, colori, font e riferimenti visivi (upload file in arrivo).
      </p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessun asset ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.name}</div>
                <div className="bi-list__item-meta">
                  {item.assetType}
                  {item.value ? ` · ${item.value}` : ""}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="assetName">Nome *</label>
            <input id="assetName" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="gcr-field">
            <label htmlFor="assetType">Tipo</label>
            <select
              id="assetType"
              value={assetType}
              onChange={(e) => setAssetType(e.target.value as typeof assetType)}
              style={{ width: "100%" }}
            >
              <option value="logo">Logo</option>
              <option value="color">Colore</option>
              <option value="font">Font</option>
              <option value="image">Immagine</option>
              <option value="other">Altro</option>
            </select>
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="assetValue">Valore / URL</label>
            <input
              id="assetValue"
              placeholder="Es. #1a1a2e o https://..."
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi asset"}
          </button>
        </div>
      </form>
    </div>
  );
}
