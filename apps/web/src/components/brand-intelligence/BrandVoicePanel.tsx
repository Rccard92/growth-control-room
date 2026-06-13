import { FormEvent, useState } from "react";
import type { BrandVoice } from "@gcr/shared";
import { useBrandVoice, useUpdateBrandVoice } from "../../hooks/useBrandIntelligence";

interface BrandVoicePanelProps {
  projectId: string;
}

function parseList(value: string): string[] {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function BrandVoicePanel({ projectId }: BrandVoicePanelProps) {
  const { data, isLoading } = useBrandVoice(projectId);
  const update = useUpdateBrandVoice(projectId);
  const [form, setForm] = useState<Partial<BrandVoice>>({});
  const [wordsToUseText, setWordsToUseText] = useState("");
  const [wordsToAvoidText, setWordsToAvoidText] = useState("");

  const values = { ...data, ...form };

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    update.mutate({
      tone: values.tone ?? undefined,
      styleNotes: values.styleNotes ?? undefined,
      formalityLevel: values.formalityLevel ?? undefined,
      emojiPolicy: values.emojiPolicy ?? undefined,
      wordsToUse: wordsToUseText ? parseList(wordsToUseText) : values.wordsToUse ?? undefined,
      wordsToAvoid: wordsToAvoidText ? parseList(wordsToAvoidText) : values.wordsToAvoid ?? undefined,
    });
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-panel">
      <h3 className="bi-panel__title">Voice & Tone</h3>
      <p className="bi-panel__subtitle">Come il brand parla: tono, stile e parole da usare o evitare.</p>
      <form onSubmit={handleSubmit}>
        <div className="bi-form-grid">
          <div className="gcr-field">
            <label htmlFor="tone">Tono *</label>
            <input
              id="tone"
              placeholder="Es. caldo, autentico, premium"
              value={values.tone ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, tone: e.target.value }))}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="formalityLevel">Formalità</label>
            <input
              id="formalityLevel"
              placeholder="Es. informale, professionale"
              value={values.formalityLevel ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, formalityLevel: e.target.value }))}
            />
          </div>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="styleNotes">Note di stile</label>
            <textarea
              id="styleNotes"
              rows={3}
              value={values.styleNotes ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, styleNotes: e.target.value }))}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="wordsToUse">Parole da usare</label>
            <input
              id="wordsToUse"
              placeholder="Separate da virgola"
              defaultValue={(values.wordsToUse ?? []).join(", ")}
              onChange={(e) => setWordsToUseText(e.target.value)}
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="wordsToAvoid">Parole da evitare</label>
            <input
              id="wordsToAvoid"
              placeholder="Separate da virgola"
              defaultValue={(values.wordsToAvoid ?? []).join(", ")}
              onChange={(e) => setWordsToAvoidText(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-save-bar">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
            {update.isPending ? "Salvataggio…" : "Salva voice"}
          </button>
        </div>
      </form>
    </div>
  );
}
