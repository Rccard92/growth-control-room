import { FormEvent, useState } from "react";
import type { BrandProfile } from "@gcr/shared";
import { useBrandProfile, useUpdateBrandProfile } from "../../hooks/useBrandIntelligence";

interface BrandProfilePanelProps {
  projectId: string;
}

export function BrandProfilePanel({ projectId }: BrandProfilePanelProps) {
  const { data, isLoading } = useBrandProfile(projectId);
  const update = useUpdateBrandProfile(projectId);
  const [form, setForm] = useState<Partial<BrandProfile>>({});

  const values = { ...data, ...form };

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    update.mutate({
      brandName: values.brandName ?? undefined,
      websiteUrl: values.websiteUrl ?? undefined,
      industry: values.industry ?? undefined,
      country: values.country ?? undefined,
      shortDescription: values.shortDescription ?? undefined,
      story: values.story ?? undefined,
      mission: values.mission ?? undefined,
    });
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Brand Profile</h3>
      <p className="bi-panel__subtitle">Identità del brand: nome, settore, storia e valori.</p>
      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="brandName">Nome brand *</label>
            <input
              id="brandName"
              value={values.brandName ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, brandName: e.target.value }))}
              required
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="websiteUrl">Sito web</label>
            <input
              id="websiteUrl"
              value={values.websiteUrl ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, websiteUrl: e.target.value }))}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="industry">Settore</label>
            <input
              id="industry"
              value={values.industry ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="country">Paese</label>
            <input
              id="country"
              value={values.country ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="shortDescription">Descrizione breve *</label>
            <textarea
              id="shortDescription"
              rows={3}
              value={values.shortDescription ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, shortDescription: e.target.value }))}
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="story">Storia del brand</label>
            <textarea
              id="story"
              rows={4}
              value={values.story ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, story: e.target.value }))}
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="mission">Missione</label>
            <textarea
              id="mission"
              rows={2}
              value={values.mission ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, mission: e.target.value }))}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
            {update.isPending ? "Salvataggio…" : "Salva profilo"}
          </button>
          {update.isSuccess && <span className="bi-panel__subtitle">Salvato</span>}
        </div>
      </form>
    </div>
  );
}
