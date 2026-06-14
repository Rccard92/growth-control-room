import { FormEvent, useEffect, useState } from "react";
import type { BrandEditorialGuidelines, BrandPersonEntry, DefaultArticleLength } from "@gcr/shared";
import { AutoResizeTextarea } from "../ui/AutoResizeTextarea";
import { AppSelect } from "../ui/AppSelect";
import {
  useBrandEditorialGuidelines,
  useUpdateBrandEditorialGuidelines,
} from "../../hooks/useBrandIntelligence";

interface BrandEditorialGuidelinesPanelProps {
  projectId: string;
}

const LIST_FIELDS = [
  ["storytellingRules", "Regole storytelling (una per riga)"],
  ["authorVoiceRules", "Regole voce autore (una per riga)"],
  ["communityCtaRules", "Regole CTA community (una per riga)"],
  ["articleDos", "Cose da fare negli articoli (una per riga)"],
  ["articleDonts", "Cose da evitare negli articoli (una per riga)"],
] as const;

const LENGTH_OPTIONS = [
  { value: "breve", label: "Breve" },
  { value: "medio", label: "Medio" },
  { value: "approfondito", label: "Approfondito" },
];

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function emptyPerson(): BrandPersonEntry {
  return { name: "", role: "", whenToUse: "", tone: "" };
}

function rowToForm(row: BrandEditorialGuidelines): Partial<BrandEditorialGuidelines> {
  return {
    contentPhilosophy: row.contentPhilosophy ?? "",
    articleLengthPolicy: row.articleLengthPolicy ?? "",
    readingStyle: row.readingStyle ?? "",
    storytellingRules: row.storytellingRules ?? [],
    brandPeople: row.brandPeople?.length ? row.brandPeople : [emptyPerson()],
    authorVoiceRules: row.authorVoiceRules ?? [],
    communityCtaRules: row.communityCtaRules ?? [],
    articleDos: row.articleDos ?? [],
    articleDonts: row.articleDonts ?? [],
    defaultArticleLength: row.defaultArticleLength ?? "medio",
  };
}

export function BrandEditorialGuidelinesPanel({ projectId }: BrandEditorialGuidelinesPanelProps) {
  const { data: guidelines, isLoading } = useBrandEditorialGuidelines(projectId);
  const update = useUpdateBrandEditorialGuidelines(projectId);
  const [form, setForm] = useState<Partial<BrandEditorialGuidelines>>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!guidelines) return;
    setForm(rowToForm(guidelines));
  }, [guidelines]);

  function patch(partial: Partial<BrandEditorialGuidelines>) {
    setForm((prev) => ({ ...prev, ...partial }));
  }

  function updatePerson(index: number, partial: Partial<BrandPersonEntry>) {
    const people = [...(form.brandPeople ?? [])];
    people[index] = { ...people[index], ...partial };
    patch({ brandPeople: people });
  }

  function addPerson() {
    patch({ brandPeople: [...(form.brandPeople ?? []), emptyPerson()] });
  }

  function removePerson(index: number) {
    const people = [...(form.brandPeople ?? [])];
    if (people.length <= 1) return;
    people.splice(index, 1);
    patch({ brandPeople: people });
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    const brandPeople = (form.brandPeople ?? []).filter((p) => p.name.trim());
    update.mutate(
      {
        contentPhilosophy: form.contentPhilosophy || null,
        articleLengthPolicy: form.articleLengthPolicy || null,
        readingStyle: form.readingStyle || null,
        storytellingRules: form.storytellingRules ?? [],
        brandPeople,
        authorVoiceRules: form.authorVoiceRules ?? [],
        communityCtaRules: form.communityCtaRules ?? [],
        articleDos: form.articleDos ?? [],
        articleDonts: form.articleDonts ?? [],
        defaultArticleLength: (form.defaultArticleLength as DefaultArticleLength) ?? "medio",
      },
      {
        onSuccess: () => setSuccessMessage("Editorial Guidelines salvate."),
        onError: () => setError("Salvataggio non riuscito. Riprova."),
      },
    );
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <form className="bi-profile-v1" onSubmit={handleSubmit}>
      {error && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      {successMessage && (
        <div className="gcr-alert gcr-alert--success" style={{ marginBottom: "1rem" }}>
          {successMessage}
        </div>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Filosofia e stile</h3>
        <p className="bi-panel__subtitle">
          Definisce come scrivere articoli umani, brevi e utili — usato dal Article Generator e
          dal contesto AI.
        </p>

        <AutoResizeTextarea
          label="Filosofia contenuti"
          value={form.contentPhilosophy ?? ""}
          onChange={(contentPhilosophy) => patch({ contentPhilosophy })}
          minRows={3}
          maxRows={8}
        />

        <AutoResizeTextarea
          label="Politica lunghezza articoli"
          value={form.articleLengthPolicy ?? ""}
          onChange={(articleLengthPolicy) => patch({ articleLengthPolicy })}
          minRows={2}
          maxRows={6}
        />

        <AutoResizeTextarea
          label="Stile di lettura"
          value={form.readingStyle ?? ""}
          onChange={(readingStyle) => patch({ readingStyle })}
          minRows={2}
          maxRows={6}
        />

        <div className="gcr-field">
          <span className="gcr-field__label">Lunghezza predefinita</span>
          <AppSelect
            value={form.defaultArticleLength ?? "medio"}
            options={LENGTH_OPTIONS}
            onChange={(value) =>
              patch({ defaultArticleLength: value as DefaultArticleLength })
            }
          />
        </div>
      </section>

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Persone del brand</h3>
        <p className="bi-panel__subtitle">
          Nome, ruolo e quando citarli negli articoli (es. firma &quot;A cura di…&quot;).
        </p>

        {(form.brandPeople ?? []).map((person, index) => (
          <div key={index} className="gcr-card" style={{ marginBottom: "1rem", padding: "1rem" }}>
            <div className="gcr-field">
              <span className="gcr-field__label">Nome</span>
              <input
                className="gcr-input"
                value={person.name}
                onChange={(e) => updatePerson(index, { name: e.target.value })}
              />
            </div>
            <div className="gcr-field">
              <span className="gcr-field__label">Ruolo</span>
              <input
                className="gcr-input"
                value={person.role}
                onChange={(e) => updatePerson(index, { role: e.target.value })}
              />
            </div>
            <AutoResizeTextarea
              label="Quando usarlo"
              value={person.whenToUse}
              onChange={(whenToUse) => updatePerson(index, { whenToUse })}
              minRows={1}
              maxRows={3}
            />
            <AutoResizeTextarea
              label="Tono"
              value={person.tone}
              onChange={(tone) => updatePerson(index, { tone })}
              minRows={1}
              maxRows={3}
            />
            {(form.brandPeople?.length ?? 0) > 1 && (
              <button
                type="button"
                className="gcr-btn gcr-btn--ghost"
                onClick={() => removePerson(index)}
              >
                Rimuovi persona
              </button>
            )}
          </div>
        ))}

        <button type="button" className="gcr-btn gcr-btn--ghost" onClick={addPerson}>
          Aggiungi persona
        </button>
      </section>

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Regole editoriali</h3>
        {LIST_FIELDS.map(([key, label]) => (
          <AutoResizeTextarea
            key={key}
            label={label}
            value={listToLines(form[key] as string[] | undefined)}
            onChange={(text) => patch({ [key]: linesToList(text) })}
            minRows={3}
            maxRows={10}
          />
        ))}
      </section>

      <div className="bi-profile-block__actions">
        <button
          type="submit"
          className="gcr-btn gcr-btn--primary"
          disabled={update.isPending}
        >
          {update.isPending ? "Salvataggio…" : "Salva Editorial Guidelines"}
        </button>
      </div>
    </form>
  );
}
