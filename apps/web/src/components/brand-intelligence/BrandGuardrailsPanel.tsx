import { FormEvent, useState } from "react";
import { useBrandGuardrails, useCreateBrandGuardrail } from "../../hooks/useBrandIntelligence";

interface BrandGuardrailsPanelProps {
  projectId: string;
}

export function BrandGuardrailsPanel({ projectId }: BrandGuardrailsPanelProps) {
  const { data: items = [], isLoading } = useBrandGuardrails(projectId);
  const create = useCreateBrandGuardrail(projectId);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [ruleType, setRuleType] = useState<"must" | "must_not" | "caution">("must_not");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    create.mutate(
      { title: title.trim(), description: description.trim() || undefined, ruleType },
      { onSuccess: () => { setTitle(""); setDescription(""); } },
    );
  }

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">AI Guardrails</h3>
      <p className="bi-panel__subtitle">Regole che l&apos;AI deve rispettare nella generazione contenuti.</p>

      {isLoading ? (
        <p className="bi-panel__subtitle">Caricamento…</p>
      ) : (
        <div className="bi-list">
          {items.length === 0 && <p className="bi-panel__subtitle">Nessun guardrail ancora.</p>}
          {items.map((item) => (
            <div key={item.id} className="bi-list__item">
              <div>
                <div className="bi-list__item-title">{item.title}</div>
                <div className="bi-list__item-meta">{item.ruleType}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="guardTitle">Titolo *</label>
            <input id="guardTitle" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="gcr-field">
            <label htmlFor="guardType">Tipo</label>
            <select
              id="guardType"
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value as typeof ruleType)}
              style={{ width: "100%" }}
            >
              <option value="must_not">Non fare (must_not)</option>
              <option value="must">Obbligatorio (must)</option>
              <option value="caution">Cautela</option>
            </select>
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="guardDesc">Descrizione</label>
            <textarea
              id="guardDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={create.isPending}>
            {create.isPending ? "Aggiunta…" : "Aggiungi guardrail"}
          </button>
        </div>
      </form>
    </div>
  );
}
