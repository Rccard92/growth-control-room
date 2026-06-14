import type { ReactNode } from "react";
import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge, fieldStatusNote } from "./SeoFieldStatusBadge";
import { SeoImagesEditor } from "./SeoImagesEditor";
import type { FieldState, FieldStateMap, SeoEditableField } from "./seoFieldState";
import type { SeoFormValues } from "./seoFormValues";
import { getUniqueFieldHelperText } from "./seoFormValues";

interface SeoFieldEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  fieldStateMap?: FieldStateMap;
  mediaImages?: Record<string, unknown>[];
  openaiConfigured?: boolean;
  missingAltCount?: number;
  batchAltLoading?: boolean;
  onChange: (key: string, value: unknown) => void;
  onImageAltChange?: (index: number, alt: string) => void;
  onGenerateField?: (field: SeoEditableField, imageId?: string) => void;
  onGenerateMissingAlts?: () => void;
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
  const statusNote = fieldStatusNote(field, value, issues, scoreBreakdown, undefined, fieldState);
  const helperText = getUniqueFieldHelperText(fieldState, statusNote);
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
      {helperText && <span className="seo-field-editor__note">{helperText}</span>}
    </label>
  );
}

function FlatSection({ children }: { children: ReactNode }) {
  return <div className="seo-field-section__fields">{children}</div>;
}

export function SeoFieldEditor({
  entityType,
  values,
  issues,
  scoreBreakdown,
  fieldStateMap,
  mediaImages = [],
  openaiConfigured,
  missingAltCount = 0,
  batchAltLoading = false,
  onChange,
  onImageAltChange,
  onGenerateField,
  onGenerateMissingAlts,
  onRestoreField,
  onAcceptField,
}: SeoFieldEditorProps) {
  return (
    <div className="seo-field-editor">
      <FlatSection>
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
        <SeoImagesEditor
          entityType={entityType}
          values={values}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          mediaImages={mediaImages}
          fieldStateMap={fieldStateMap}
          openaiConfigured={openaiConfigured}
          missingAltCount={missingAltCount}
          batchAltLoading={batchAltLoading}
          onChange={onChange}
          onImageAltChange={onImageAltChange}
          onGenerateField={onGenerateField}
          onGenerateMissingAlts={onGenerateMissingAlts}
          onRestoreField={onRestoreField}
          onAcceptField={onAcceptField}
        />
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
        <FieldRow
          label="Handle URL"
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
      </FlatSection>
    </div>
  );
}
