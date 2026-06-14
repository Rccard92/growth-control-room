import type { EditorialBriefPayload } from "@gcr/shared";
import { listToTextarea, textareaToList } from "./editorial-brief-utils";

interface EditorialBriefEditorProps {
  value: EditorialBriefPayload;
  onChange: (value: EditorialBriefPayload) => void;
  readOnlyWarnings?: boolean;
}

function ListTextarea({
  label,
  value,
  onChange,
  rows = 4,
}: {
  label: string;
  value: string[];
  onChange: (next: string[]) => void;
  rows?: number;
}) {
  return (
    <label className="gcr-field">
      <span className="gcr-field__label">{label}</span>
      <textarea
        className="gcr-input editorial-brief-editor__list"
        rows={rows}
        value={listToTextarea(value)}
        onChange={(e) => onChange(textareaToList(e.target.value))}
        placeholder="Un elemento per riga"
      />
    </label>
  );
}

export function EditorialBriefEditor({
  value,
  onChange,
  readOnlyWarnings = true,
}: EditorialBriefEditorProps) {
  function patch(partial: Partial<EditorialBriefPayload>) {
    onChange({ ...value, ...partial });
  }

  return (
    <div className="editorial-brief-editor">
      <label className="gcr-field">
        <span className="gcr-field__label">Titolo proposto</span>
        <input
          className="gcr-input"
          value={value.proposedTitle}
          onChange={(e) => patch({ proposedTitle: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Intento di ricerca</span>
        <input
          className="gcr-input"
          value={value.searchIntent}
          onChange={(e) => patch({ searchIntent: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Target</span>
        <input
          className="gcr-input"
          value={value.targetAudience}
          onChange={(e) => patch({ targetAudience: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Keyword principale</span>
        <input
          className="gcr-input"
          value={value.primaryKeyword}
          onChange={(e) => patch({ primaryKeyword: e.target.value })}
        />
      </label>

      <ListTextarea
        label="Keyword secondarie"
        value={value.secondaryKeywords}
        onChange={(secondaryKeywords) => patch({ secondaryKeywords })}
        rows={2}
      />

      <label className="gcr-field">
        <span className="gcr-field__label">Angolo contenuto</span>
        <textarea
          className="gcr-input"
          rows={2}
          value={value.contentAngle}
          onChange={(e) => patch({ contentAngle: e.target.value })}
        />
      </label>

      <ListTextarea
        label="Struttura H2/H3"
        value={value.h2H3Structure}
        onChange={(h2H3Structure) => patch({ h2H3Structure })}
      />

      <ListTextarea
        label="Prodotti da linkare"
        value={value.productsToLink}
        onChange={(productsToLink) => patch({ productsToLink })}
        rows={3}
      />

      <ListTextarea
        label="FAQ da includere"
        value={value.faqToInclude}
        onChange={(faqToInclude) => patch({ faqToInclude })}
        rows={3}
      />

      <ListTextarea
        label="Claim da evitare"
        value={value.claimsToAvoid}
        onChange={(claimsToAvoid) => patch({ claimsToAvoid })}
        rows={3}
      />

      <ListTextarea
        label="Claim sicuri da usare"
        value={value.safeClaimsToUse}
        onChange={(safeClaimsToUse) => patch({ safeClaimsToUse })}
        rows={3}
      />

      <label className="gcr-field">
        <span className="gcr-field__label">CTA consigliata</span>
        <input
          className="gcr-input"
          value={value.recommendedCta}
          onChange={(e) => patch({ recommendedCta: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Meta title</span>
        <input
          className="gcr-input"
          value={value.metaTitle}
          onChange={(e) => patch({ metaTitle: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Meta description</span>
        <textarea
          className="gcr-input"
          rows={3}
          value={value.metaDescription}
          onChange={(e) => patch({ metaDescription: e.target.value })}
        />
      </label>

      <ListTextarea
        label="Suggerimenti internal link"
        value={value.internalLinksSuggestions}
        onChange={(internalLinksSuggestions) => patch({ internalLinksSuggestions })}
        rows={3}
      />

      <label className="gcr-field">
        <span className="gcr-field__label">Note operative</span>
        <textarea
          className="gcr-input"
          rows={3}
          value={value.notes}
          onChange={(e) => patch({ notes: e.target.value })}
        />
      </label>

      {value.brandContextUsed.length > 0 && (
        <div className="editorial-brief-editor__meta">
          <span className="gcr-field__label">Contesto brand usato</span>
          <ul className="editorial-brief-editor__tags">
            {value.brandContextUsed.map((tag) => (
              <li key={tag}>{tag}</li>
            ))}
          </ul>
        </div>
      )}

      {readOnlyWarnings && value.warnings.length > 0 && (
        <div className="gcr-alert gcr-alert--warn editorial-brief-editor__warnings">
          <span className="gcr-field__label">Warning</span>
          <ul>
            {value.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
