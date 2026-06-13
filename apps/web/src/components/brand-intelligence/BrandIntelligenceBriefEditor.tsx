import { useEffect, useState } from "react";
import type { BrandBriefPayload } from "@gcr/shared";

const SECTIONS: Array<{ key: string; label: string; type: "object" | "array" | "lists" }> = [
  { key: "brand_identity", label: "Identità brand", type: "object" },
  { key: "voice_and_tone", label: "Voice & Tone", type: "lists" },
  { key: "products_and_categories", label: "Prodotti e categorie", type: "array" },
  { key: "audience", label: "Audience", type: "array" },
  { key: "questions_objections_feedback", label: "Domande, obiezioni e feedback", type: "lists" },
  { key: "claims_compliance", label: "Claims & Compliance", type: "lists" },
  { key: "seo_guidelines", label: "SEO Guidelines", type: "lists" },
  { key: "content_pillars", label: "Content Pillars", type: "array" },
  { key: "ads_social_guidelines", label: "Ads / Social Guidelines", type: "lists" },
  { key: "ai_guardrails", label: "AI Guardrails", type: "lists" },
  { key: "missing_information", label: "Informazioni mancanti", type: "array" },
];

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

function listToLines(items: unknown): string {
  if (!Array.isArray(items)) return "";
  return items.map((i) => (typeof i === "string" ? i : JSON.stringify(i))).join("\n");
}

interface BrandIntelligenceBriefEditorProps {
  payload: BrandBriefPayload;
  onChange: (payload: BrandBriefPayload) => void;
  readOnly?: boolean;
}

export function BrandIntelligenceBriefEditor({
  payload,
  onChange,
  readOnly = false,
}: BrandIntelligenceBriefEditorProps) {
  const [local, setLocal] = useState<BrandBriefPayload>(payload);

  useEffect(() => {
    setLocal(payload);
  }, [payload]);

  function update(next: BrandBriefPayload) {
    setLocal(next);
    onChange(next);
  }

  function updateObjectSection(sectionKey: string, field: string, value: string) {
    const section = { ...((local[sectionKey] as Record<string, unknown>) || {}) };
    section[field] = value;
    update({ ...local, [sectionKey]: section });
  }

  function updateListSection(sectionKey: string, field: string, text: string) {
    const section = { ...((local[sectionKey] as Record<string, unknown>) || {}) };
    section[field] = linesToList(text);
    update({ ...local, [sectionKey]: section });
  }

  function updateJsonSection(sectionKey: string, text: string) {
    try {
      const parsed = JSON.parse(text || "[]");
      update({ ...local, [sectionKey]: parsed });
    } catch {
      // keep typing
    }
  }

  return (
    <div className="bi-brief-editor">
      {SECTIONS.map((section) => {
        const data = local[section.key];
        return (
          <details key={section.key} className="bi-brief-editor__section" open>
            <summary className="bi-brief-editor__section-title">{section.label}</summary>
            <div className="bi-brief-editor__section-body">
              {section.type === "object" && typeof data === "object" && data !== null && (
                <div className="bi-form-grid">
                  {Object.entries(data as Record<string, unknown>).map(([field, val]) =>
                    Array.isArray(val) ? (
                      <label key={field} className="gcr-field bi-brief-editor__field--full">
                        <span>{field}</span>
                        <textarea
                          rows={3}
                          disabled={readOnly}
                          value={listToLines(val)}
                          onChange={(e) => updateListSection(section.key, field, e.target.value)}
                        />
                      </label>
                    ) : (
                      <label key={field} className="gcr-field">
                        <span>{field}</span>
                        <textarea
                          rows={field.includes("description") || field === "story" ? 4 : 2}
                          disabled={readOnly}
                          value={String(val ?? "")}
                          onChange={(e) => updateObjectSection(section.key, field, e.target.value)}
                        />
                      </label>
                    ),
                  )}
                </div>
              )}

              {section.type === "lists" && typeof data === "object" && data !== null && (
                <div className="bi-form-grid">
                  {Object.entries(data as Record<string, unknown>).map(([field, val]) => (
                    <label key={field} className="gcr-field bi-brief-editor__field--full">
                      <span>{field}</span>
                      <textarea
                        rows={4}
                        disabled={readOnly}
                        value={listToLines(val)}
                        onChange={(e) => updateListSection(section.key, field, e.target.value)}
                      />
                    </label>
                  ))}
                </div>
              )}

              {(section.type === "array" || section.key === "missing_information") && (
                <label className="gcr-field bi-brief-editor__field--full">
                  <span>Contenuto (JSON o una riga per elemento)</span>
                  <textarea
                    rows={8}
                    disabled={readOnly}
                    value={
                      section.key === "missing_information"
                        ? listToLines(data)
                        : JSON.stringify(data ?? [], null, 2)
                    }
                    onChange={(e) => {
                      if (section.key === "missing_information") {
                        update({ ...local, missing_information: linesToList(e.target.value) });
                      } else {
                        updateJsonSection(section.key, e.target.value);
                      }
                    }}
                  />
                </label>
              )}
            </div>
          </details>
        );
      })}
    </div>
  );
}
