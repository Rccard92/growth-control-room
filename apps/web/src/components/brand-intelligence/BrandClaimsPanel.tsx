import { FormEvent, useState } from "react";
import { useBrandClaims, useCreateBrandClaim } from "../../hooks/useBrandIntelligence";

interface BrandClaimsPanelProps {
  projectId: string;
}

export function BrandClaimsPanel({ projectId }: BrandClaimsPanelProps) {
  const { data: items = [], isLoading } = useBrandClaims(projectId);
  const create = useCreateBrandClaim(projectId);
  const [title, setTitle] = useState("");
  const [ruleType, setRuleType] = useState<"forbidden" | "caution" | "allowed" | "disclaimer">(
    "forbidden",
  );
  const [description, setDescription] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    create.mutate(
      {
        title: title.trim(),
        ruleType,
        description: description.trim() || undefined,
        severity: ruleType === "forbidden" ? "critical" : "warning",
      },
      { onSuccess: () => { setTitle(""); setDescription(""); } },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Claims & Compliance</h3>
      <p className="bi-panel__subtitle">Regole su affermazioni consentite, vietate o da usare con cautela.</p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessuna regola ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.title}</div>
                <div className="bi-list__item-meta">
                  {item.ruleType} · {item.severity}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="claimTitle">Titolo *</label>
            <input id="claimTitle" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="gcr-field">
            <label htmlFor="ruleType">Tipo</label>
            <select
              id="ruleType"
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value as typeof ruleType)}
              style={{ width: "100%" }}
            >
              <option value="forbidden">Vietato</option>
              <option value="caution">Cautela</option>
              <option value="allowed">Consentito</option>
              <option value="disclaimer">Disclaimer</option>
            </select>
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="claimDesc">Descrizione</label>
            <textarea
              id="claimDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi regola"}
          </button>
        </div>
      </form>
    </div>
  );
}
