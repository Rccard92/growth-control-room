import { FormEvent, useState } from "react";
import {
  useBrandProducts,
  useCreateBrandProduct,
} from "../../hooks/useBrandIntelligence";

interface BrandProductsPanelProps {
  projectId: string;
}

export function BrandProductsPanel({ projectId }: BrandProductsPanelProps) {
  const { data: items = [], isLoading } = useBrandProducts(projectId);
  const create = useCreateBrandProduct(projectId);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entityType, setEntityType] = useState<"product" | "category">("product");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate(
      { name: name.trim(), description: description.trim() || undefined, entityType },
      {
        onSuccess: () => {
          setName("");
          setDescription("");
        },
      },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Products & Categories</h3>
      <p className="bi-panel__subtitle">Conoscenza prodotti e categorie per contenuti accurati.</p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessun elemento ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.name}</div>
                <div className="bi-list__item-meta">
                  {item.entityType === "product" ? "Prodotto" : "Categoria"}
                  {item.description ? ` · ${item.description.slice(0, 80)}` : ""}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="productName">Nome *</label>
            <input id="productName" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="gcr-field">
            <label htmlFor="entityType">Tipo</label>
            <select
              id="entityType"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as "product" | "category")}
              style={{ width: "100%" }}
            >
              <option value="product">Prodotto</option>
              <option value="category">Categoria</option>
            </select>
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="productDesc">Descrizione</label>
            <textarea
              id="productDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi"}
          </button>
        </div>
      </form>
    </div>
  );
}
