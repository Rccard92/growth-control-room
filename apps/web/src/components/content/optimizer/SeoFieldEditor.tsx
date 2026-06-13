import type { ReactNode } from "react";
import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge, fieldStatusNote } from "./SeoFieldStatusBadge";
import type { FieldState, FieldStateMap, SeoEditableField } from "./seoFieldState";
import type { SeoFormValues } from "./seoFormValues";

interface SeoFieldEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  fieldStateMap?: FieldStateMap;
  openaiConfigured?: boolean;
  onChange: (key: string, value: unknown) => void;
  onGenerateField?: (field: SeoEditableField) => void;
  onRestoreField?: (field: string) => void;
  onAcceptField?: (field: string) => void;
}

function FieldRow({
  label,
  field,
  value,
  issues,
  scoreBreakdown,
  fieldState,
  openaiConfigured,
  onChange,
  onGenerateField,
  onRestoreField,
  onAcceptField,
  multiline,
}: {
  label: string;
  field: SeoEditableField;
  value: string;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  fieldState?: FieldState;
  openaiConfigured?: boolean;
  onChange: (key: string, value: string) => void;
  onGenerateField?: (field: SeoEditableField) => void;
  onRestoreField?: (field: string) => void;
  onAcceptField?: (field: string) => void;
  multiline?: boolean;
}) {
  const note = fieldStatusNote(field, value, issues, scoreBreakdown, undefined, fieldState);
  const showRestore = fieldState?.dirty && fieldState.value !== fieldState.originalValue;
  const showAccept =
    fieldState?.source === "ai" && !fieldState.accepted && fieldState.dirty;

  return (
    <label className="seo-field-editor__field">
      <span className="seo-field-editor__label">
        {label}
        <SeoFieldStatusBadge
          field={field}
          value={value}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldState}
        />
        <span className="seo-field-editor__actions">
          {openaiConfigured && onGenerateField && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm seo-field-ai-btn"
              title="Genera solo questo campo"
              disabled={fieldState?.generating}
              onClick={(e) => {
                e.preventDefault();
                onGenerateField(field);
              }}
            >
              {fieldState?.generating ? "…" : "✦ AI"}
            </button>
          )}
          {showRestore && onRestoreField && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={(e) => {
                e.preventDefault();
                onRestoreField(field);
              }}
            >
              Ripristina
            </button>
          )}
          {showAccept && onAcceptField && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={(e) => {
                e.preventDefault();
                onAcceptField(field);
              }}
            >
              Accetta
            </button>
          )}
        </span>
      </span>
      {multiline ? (
        <textarea
          className="seo-field-editor__input"
          rows={4}
          value={value}
          disabled={fieldState?.generating}
          onChange={(e) => onChange(field, e.target.value)}
        />
      ) : (
        <input
          className="seo-field-editor__input"
          type="text"
          value={value}
          disabled={fieldState?.generating}
          onChange={(e) => onChange(field, e.target.value)}
        />
      )}
      {note && <span className="seo-field-editor__note">{note}</span>}
    </label>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="seo-field-section">
      <h4 className="seo-field-section__title">{title}</h4>
      <div className="seo-field-section__fields">{children}</div>
    </section>
  );
}

export function SeoFieldEditor({
  entityType,
  values,
  issues,
  scoreBreakdown,
  fieldStateMap,
  openaiConfigured,
  onChange,
  onGenerateField,
  onRestoreField,
  onAcceptField,
}: SeoFieldEditorProps) {
  return (
    <div className="seo-field-editor">
      <Section title="Identità prodotto/categoria">
        <FieldRow
          label={entityType === "product" ? "Titolo prodotto" : "Titolo collection"}
          field="title"
          value={String(values.title ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldStateMap?.title}
          openaiConfigured={openaiConfigured}
          onChange={onChange}
          onGenerateField={onGenerateField}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
        />
        <FieldRow
          label="Handle"
          field="handle"
          value={String(values.handle ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldStateMap?.handle}
          openaiConfigured={openaiConfigured}
          onChange={onChange}
          onGenerateField={onGenerateField}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
        />
        {entityType === "product" && (
          <>
            <div className="seo-field-editor__readonly">
              <span className="seo-field-editor__label">Product type</span>
              <span className="seo-field-editor__readonly-value">
                {String(values.productType ?? "—")}
              </span>
            </div>
            <div className="seo-field-editor__readonly">
              <span className="seo-field-editor__label">Vendor</span>
              <span className="seo-field-editor__readonly-value">
                {String(values.vendor ?? "—")}
              </span>
            </div>
          </>
        )}
      </Section>

      <Section title="Metadata SEO">
        <FieldRow
          label="SEO title"
          field="seoTitle"
          value={String(values.seoTitle ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldStateMap?.seoTitle}
          openaiConfigured={openaiConfigured}
          onChange={onChange}
          onGenerateField={onGenerateField}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
        />
        <FieldRow
          label="Meta description"
          field="metaDescription"
          value={String(values.metaDescription ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldStateMap?.metaDescription}
          openaiConfigured={openaiConfigured}
          onChange={onChange}
          onGenerateField={onGenerateField}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
          multiline
        />
      </Section>

      <Section title="Contenuto">
        <FieldRow
          label="Descrizione (HTML)"
          field="descriptionHtml"
          value={String(values.descriptionHtml ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          fieldState={fieldStateMap?.descriptionHtml}
          openaiConfigured={openaiConfigured}
          onChange={onChange}
          onGenerateField={onGenerateField}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
          multiline
        />
      </Section>
    </div>
  );
}
