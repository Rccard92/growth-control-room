import { FormEvent, useEffect, useState } from "react";
import type { BrandIdentity } from "@gcr/shared";
import { useBrandIdentity, useUpdateBrandIdentity } from "../../hooks/useBrandIntelligence";

interface BrandIdentityPanelProps {
  projectId: string;
}

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

const EMPTY_FORM: Partial<BrandIdentity> = {
  positioning: "",
  brandValues: [],
  differentiators: [],
  productionPrinciples: [],
  qualityPrinciples: [],
  trustElements: [],
  whatBrandIs: "",
  whatBrandIsNot: "",
  storytellingNotes: "",
};

export function BrandIdentityPanel({ projectId }: BrandIdentityPanelProps) {
  const { data: identity, isLoading } = useBrandIdentity(projectId);
  const update = useUpdateBrandIdentity(projectId);
  const [form, setForm] = useState<Partial<BrandIdentity>>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!identity) return;
    setForm({
      positioning: identity.positioning ?? "",
      brandValues: identity.brandValues ?? [],
      differentiators: identity.differentiators ?? [],
      productionPrinciples: identity.productionPrinciples ?? [],
      qualityPrinciples: identity.qualityPrinciples ?? [],
      trustElements: identity.trustElements ?? [],
      whatBrandIs: identity.whatBrandIs ?? "",
      whatBrandIsNot: identity.whatBrandIsNot ?? "",
      storytellingNotes: identity.storytellingNotes ?? "",
    });
  }, [identity]);

  function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    update.mutate(
      {
        positioning: form.positioning || undefined,
        brandValues: form.brandValues?.length ? form.brandValues : undefined,
        differentiators: form.differentiators?.length ? form.differentiators : undefined,
        productionPrinciples: form.productionPrinciples?.length
          ? form.productionPrinciples
          : undefined,
        qualityPrinciples: form.qualityPrinciples?.length ? form.qualityPrinciples : undefined,
        trustElements: form.trustElements?.length ? form.trustElements : undefined,
        whatBrandIs: form.whatBrandIs || undefined,
        whatBrandIsNot: form.whatBrandIsNot || undefined,
        storytellingNotes: form.storytellingNotes || undefined,
      },
      { onError: (err: Error) => setError(err.message) },
    );
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-profile-v1">
      {error && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSave}>
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Brand Identity</h3>
          <p className="bi-panel__subtitle">
            Posizionamento, valori e principi del brand. Salvataggio manuale — nessun enrich AI in
            questo step.
          </p>

          <div className="bi-form-grid">
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="positioning">Posizionamento</label>
              <textarea
                id="positioning"
                rows={3}
                value={form.positioning ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, positioning: e.target.value }))}
              />
            </div>

            {(
              [
                ["brandValues", "Valori brand (uno per riga)"],
                ["differentiators", "Differenziatori (uno per riga)"],
                ["productionPrinciples", "Principi di produzione (uno per riga)"],
                ["qualityPrinciples", "Principi di qualità (uno per riga)"],
                ["trustElements", "Elementi di fiducia (uno per riga)"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field bi-form-grid--full" key={key}>
                <label htmlFor={key}>{label}</label>
                <textarea
                  id={key}
                  rows={3}
                  value={listToLines(form[key] as string[] | undefined)}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: linesToList(e.target.value) }))}
                />
              </div>
            ))}

            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="whatBrandIs">Cosa il brand è</label>
              <textarea
                id="whatBrandIs"
                rows={3}
                value={form.whatBrandIs ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, whatBrandIs: e.target.value }))}
              />
            </div>

            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="whatBrandIsNot">Cosa il brand non è</label>
              <textarea
                id="whatBrandIsNot"
                rows={3}
                value={form.whatBrandIsNot ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, whatBrandIsNot: e.target.value }))}
              />
            </div>

            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="storytellingNotes">Note storytelling</label>
              <textarea
                id="storytellingNotes"
                rows={4}
                value={form.storytellingNotes ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, storytellingNotes: e.target.value }))}
              />
            </div>
          </div>

          <div className="bi-profile-actions">
            <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
              {update.isPending ? "Salvataggio…" : "Salva Brand Identity"}
            </button>
            {update.isSuccess && (
              <span className="bi-panel__subtitle" style={{ margin: 0 }}>
                Salvato.
              </span>
            )}
          </div>
        </section>
      </form>
    </div>
  );
}
