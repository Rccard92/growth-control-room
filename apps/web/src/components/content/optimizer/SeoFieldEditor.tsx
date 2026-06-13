import type { ReactNode } from "react";
import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge, fieldStatusNote } from "./SeoFieldStatusBadge";
import type { SeoFormValues } from "./seoFormValues";

interface SeoFieldEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  aiFilledFields?: Set<string>;
  onChange: (key: string, value: unknown) => void;
}

function FieldRow({
  label,
  field,
  value,
  issues,
  scoreBreakdown,
  aiFilledFields,
  onChange,
  multiline,
}: {
  label: string;
  field: string;
  value: string;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  aiFilledFields?: Set<string>;
  onChange: (key: string, value: string) => void;
  multiline?: boolean;
}) {
  const note = fieldStatusNote(field, value, issues, scoreBreakdown, aiFilledFields);

  return (
    <label className="seo-field-editor__field">
      <span className="seo-field-editor__label">
        {label}
        <SeoFieldStatusBadge
          field={field}
          value={value}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          aiFilledFields={aiFilledFields}
        />
      </span>
      {multiline ? (
        <textarea
          className="seo-field-editor__input"
          rows={4}
          value={value}
          onChange={(e) => onChange(field, e.target.value)}
        />
      ) : (
        <input
          className="seo-field-editor__input"
          type="text"
          value={value}
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
  aiFilledFields,
  onChange,
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
          aiFilledFields={aiFilledFields}
          onChange={onChange}
        />
        <FieldRow
          label="Handle"
          field="handle"
          value={String(values.handle ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          aiFilledFields={aiFilledFields}
          onChange={onChange}
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
          aiFilledFields={aiFilledFields}
          onChange={onChange}
        />
        <FieldRow
          label="Meta description"
          field="metaDescription"
          value={String(values.metaDescription ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
          aiFilledFields={aiFilledFields}
          onChange={onChange}
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
          aiFilledFields={aiFilledFields}
          onChange={onChange}
          multiline
        />
      </Section>
    </div>
  );
}
