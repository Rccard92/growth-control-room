import { useState } from "react";
import type { BrandSectionDraft, SectionDraftKey } from "@gcr/shared";
import { BrandOfficialVsDraftDiff } from "./BrandOfficialVsDraftDiff";

interface BrandSectionDraftEditorProps {
  draft: BrandSectionDraft;
  onSave: (payload: unknown) => void;
  saving?: boolean;
}

function tagList(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  return typeof value === "string" ? value : "";
}

function parseTags(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function BrandSectionDraftEditor({ draft, onSave, saving }: BrandSectionDraftEditorProps) {
  const [payload, setPayload] = useState<Record<string, unknown>>(
    () => (draft.draftPayload as Record<string, unknown>) ?? {},
  );
  const official = (draft.previousOfficialSnapshot as Record<string, unknown>) ?? {};
  const warnings = draft.warnings as { messages?: string[]; missingInformation?: string[] } | null;

  function setField(key: string, value: unknown) {
    setPayload((p) => ({ ...p, [key]: value }));
  }

  function renderProfile() {
    const off = (official.brand_profile as Record<string, unknown>) ?? official;
    const fields = [
      ["brand_name", "Nome brand"],
      ["short_description", "Descrizione breve"],
      ["story", "Storia"],
      ["mission", "Missione"],
      ["values", "Valori (virgola)"],
      ["differentiators", "Differenziatori (virgola)"],
    ] as const;
    return (
      <div className="bi-section-draft-editor__fields">
        {fields.map(([key, label]) => (
          <div key={key} className="bi-section-draft-editor__field">
            <BrandOfficialVsDraftDiff official={off[key]} draft={payload[key]} fieldLabel={label} />
            <label>
              {label}
              {key.includes("values") || key === "differentiators" ? (
                <input
                  value={tagList(payload[key])}
                  onChange={(e) => setField(key, parseTags(e.target.value))}
                />
              ) : (
                <textarea
                  rows={key === "short_description" ? 2 : 3}
                  value={String(payload[key] ?? "")}
                  onChange={(e) => setField(key, e.target.value)}
                />
              )}
            </label>
          </div>
        ))}
      </div>
    );
  }

  function renderVoice() {
    const off = (official.voice_tone as Record<string, unknown>) ?? official;
    return (
      <div className="bi-section-draft-editor__fields">
        {(
          [
            ["tone", "Tono"],
            ["style_notes", "Note stile"],
            ["words_to_use", "Parole da usare"],
            ["words_to_avoid", "Parole da evitare"],
          ] as const
        ).map(([key, label]) => (
          <div key={key} className="bi-section-draft-editor__field">
            <BrandOfficialVsDraftDiff official={off[key]} draft={payload[key]} fieldLabel={label} />
            <label>
              {label}
              <textarea
                rows={2}
                value={
                  key.includes("words") ? tagList(payload[key]) : String(payload[key] ?? "")
                }
                onChange={(e) =>
                  setField(
                    key,
                    key.includes("words") ? parseTags(e.target.value) : e.target.value,
                  )
                }
              />
            </label>
          </div>
        ))}
      </div>
    );
  }

  function renderClaims() {
    const lists = ["allowed", "forbidden", "caution", "disclaimers"] as const;
    const labels = {
      allowed: "Claim consentiti",
      forbidden: "Claim vietati",
      caution: "Claim con cautela",
      disclaimers: "Disclaimer",
    };
    return (
      <div className="bi-section-draft-editor__fields">
        {lists.map((key) => (
          <label key={key}>
            {labels[key]}
            <textarea
              rows={4}
              value={JSON.stringify(payload[key] ?? [], null, 2)}
              onChange={(e) => {
                try {
                  setField(key, JSON.parse(e.target.value));
                } catch {
                  /* ignore parse while typing */
                }
              }}
            />
          </label>
        ))}
      </div>
    );
  }

  function renderGenericJson() {
    return (
      <textarea
        className="bi-section-draft-editor__json"
        rows={16}
        value={JSON.stringify(payload, null, 2)}
        onChange={(e) => {
          try {
            setPayload(JSON.parse(e.target.value));
          } catch {
            /* ignore */
          }
        }}
      />
    );
  }

  const editors: Partial<Record<SectionDraftKey, () => JSX.Element>> = {
    brand_profile: renderProfile,
    voice_tone: renderVoice,
    claims_compliance: renderClaims,
  };

  return (
    <div className="bi-section-draft-editor">
      {draft.summary && <p className="bi-panel__subtitle">{draft.summary}</p>}
      {draft.confidence != null && (
        <p className="bi-section-draft-editor__meta">
          Confidence: {Math.round(draft.confidence * 100)}%
          {draft.confidence < 0.65 && <span className="bi-fact-badge bi-fact-badge--conflict"> Dedotto</span>}
        </p>
      )}
      {warnings?.messages?.map((w) => (
        <p key={w} className="bi-section-draft-editor__warning">{w}</p>
      ))}
      {warnings?.missingInformation?.map((m) => (
        <p key={m} className="bi-section-draft-editor__missing">Manca: {m}</p>
      ))}
      {(editors[draft.sectionKey] ?? renderGenericJson)()}
      <button
        type="button"
        className="gcr-btn gcr-btn--primary gcr-btn--sm"
        disabled={saving}
        onClick={() => onSave(payload)}
      >
        {saving ? "Salvataggio…" : "Salva bozza"}
      </button>
    </div>
  );
}
