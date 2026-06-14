import type { ReactNode } from "react";
import type { EditorialBriefPayload } from "@gcr/shared";
import { AutoResizeTextarea } from "../../ui/AutoResizeTextarea";
import { listToTextarea, textareaToList } from "./editorial-brief-utils";

interface EditorialBriefEditorProps {
  value: EditorialBriefPayload;
  onChange: (value: EditorialBriefPayload) => void;
  readOnlyWarnings?: boolean;
}

function BriefSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="editorial-brief-section gcr-card">
      <h5 className="editorial-brief-section__title">{title}</h5>
      <div className="editorial-brief-section__body">{children}</div>
    </section>
  );
}

function ListField({
  label,
  value,
  onChange,
  minRows = 3,
  maxRows = 12,
}: {
  label: string;
  value: string[];
  onChange: (next: string[]) => void;
  minRows?: number;
  maxRows?: number;
}) {
  return (
    <AutoResizeTextarea
      label={label}
      value={listToTextarea(value)}
      onChange={(text) => onChange(textareaToList(text))}
      minRows={minRows}
      maxRows={maxRows}
      placeholder="Un elemento per riga"
      className="editorial-brief-editor__list"
    />
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
      <BriefSection title="Strategia">
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
        <AutoResizeTextarea
          label="Angolo contenuto"
          value={value.contentAngle}
          onChange={(contentAngle) => patch({ contentAngle })}
          minRows={2}
          maxRows={8}
        />
      </BriefSection>

      <BriefSection title="Keyword">
        <label className="gcr-field">
          <span className="gcr-field__label">Keyword principale</span>
          <input
            className="gcr-input"
            value={value.primaryKeyword}
            onChange={(e) => patch({ primaryKeyword: e.target.value })}
          />
        </label>
        <ListField
          label="Keyword secondarie"
          value={value.secondaryKeywords}
          onChange={(secondaryKeywords) => patch({ secondaryKeywords })}
          minRows={2}
        />
      </BriefSection>

      <BriefSection title="Struttura">
        <ListField
          label="Struttura H2/H3"
          value={value.h2H3Structure}
          onChange={(h2H3Structure) => patch({ h2H3Structure })}
        />
      </BriefSection>

      <BriefSection title="Collegamenti e contenuti da includere">
        <ListField
          label="Prodotti da linkare"
          value={value.productsToLink}
          onChange={(productsToLink) => patch({ productsToLink })}
          minRows={2}
        />
        <ListField
          label="FAQ da includere"
          value={value.faqToInclude}
          onChange={(faqToInclude) => patch({ faqToInclude })}
          minRows={2}
        />
        <ListField
          label="Suggerimenti internal link"
          value={value.internalLinksSuggestions}
          onChange={(internalLinksSuggestions) => patch({ internalLinksSuggestions })}
          minRows={2}
        />
      </BriefSection>

      <BriefSection title="Compliance e CTA">
        <ListField
          label="Claim da evitare"
          value={value.claimsToAvoid}
          onChange={(claimsToAvoid) => patch({ claimsToAvoid })}
          minRows={2}
        />
        <ListField
          label="Claim sicuri da usare"
          value={value.safeClaimsToUse}
          onChange={(safeClaimsToUse) => patch({ safeClaimsToUse })}
          minRows={2}
        />
        <label className="gcr-field">
          <span className="gcr-field__label">CTA consigliata</span>
          <input
            className="gcr-input"
            value={value.recommendedCta}
            onChange={(e) => patch({ recommendedCta: e.target.value })}
          />
        </label>
      </BriefSection>

      <BriefSection title="Metadata">
        <label className="gcr-field">
          <span className="gcr-field__label">Meta title</span>
          <input
            className="gcr-input"
            value={value.metaTitle}
            onChange={(e) => patch({ metaTitle: e.target.value })}
          />
        </label>
        <AutoResizeTextarea
          label="Meta description"
          value={value.metaDescription}
          onChange={(metaDescription) => patch({ metaDescription })}
          minRows={2}
          maxRows={8}
        />
      </BriefSection>

      <BriefSection title="Note e warning">
        <AutoResizeTextarea
          label="Note operative"
          value={value.notes}
          onChange={(notes) => patch({ notes })}
          minRows={2}
          maxRows={10}
        />
        {readOnlyWarnings && value.warnings.length > 0 && (
          <div className="gcr-alert gcr-alert--warning editorial-brief-editor__warnings">
            <span className="gcr-field__label">Warning</span>
            <ul>
              {value.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </BriefSection>

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
    </div>
  );
}
