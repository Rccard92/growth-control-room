import { FormEvent, useState } from "react";
import type { BrandSeoStrategy } from "@gcr/shared";
import { useBrandSeoStrategy, useUpdateBrandSeoStrategy } from "../../hooks/useBrandIntelligence";

interface BrandSeoStrategyPanelProps {
  projectId: string;
}

function parseList(value: string): string[] {
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

export function BrandSeoStrategyPanel({ projectId }: BrandSeoStrategyPanelProps) {
  const { data, isLoading } = useBrandSeoStrategy(projectId);
  const update = useUpdateBrandSeoStrategy(projectId);
  const [form, setForm] = useState<Partial<BrandSeoStrategy>>({});
  const [keywordsText, setKeywordsText] = useState("");

  const values = { ...data, ...form };

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    update.mutate({
      primaryKeywords: keywordsText
        ? parseList(keywordsText)
        : values.primaryKeywords ?? undefined,
      internalLinkingNotes: values.internalLinkingNotes ?? undefined,
      metaTitlePattern: values.metaTitlePattern ?? undefined,
      metaDescriptionPattern: values.metaDescriptionPattern ?? undefined,
    });
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">SEO Strategy</h3>
      <p className="bi-panel__subtitle">Keyword prioritarie e pattern per metadata SEO.</p>
      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="primaryKeywords">Keyword primarie *</label>
            <input
              id="primaryKeywords"
              placeholder="Separate da virgola"
              defaultValue={(values.primaryKeywords ?? []).join(", ")}
              onChange={(e) => setKeywordsText(e.target.value)}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="metaTitlePattern">Pattern meta title</label>
            <input
              id="metaTitlePattern"
              value={values.metaTitlePattern ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, metaTitlePattern: e.target.value }))}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="metaDescPattern">Pattern meta description</label>
            <input
              id="metaDescPattern"
              value={values.metaDescriptionPattern ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, metaDescriptionPattern: e.target.value }))}
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="internalLinking">Note internal linking</label>
            <textarea
              id="internalLinking"
              rows={3}
              value={values.internalLinkingNotes ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, internalLinkingNotes: e.target.value }))}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
            {update.isPending ? "Salvataggio…" : "Salva strategia SEO"}
          </button>
        </div>
      </form>
    </div>
  );
}
