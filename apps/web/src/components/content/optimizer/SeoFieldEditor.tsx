import type { ReactNode } from "react";
import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge, fieldStatusNote } from "./SeoFieldStatusBadge";
import type { SeoFormValues } from "./seoFormValues";

interface SeoFieldEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  mediaImages?: Record<string, unknown>[];
  onChange: (key: string, value: unknown) => void;
  onImageAltChange?: (index: number, alt: string) => void;
}

function FieldRow({
  label,
  field,
  value,
  issues,
  scoreBreakdown,
  onChange,
  multiline,
}: {
  label: string;
  field: string;
  value: string;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  onChange: (key: string, value: string) => void;
  multiline?: boolean;
}) {
  const note = fieldStatusNote(field, value, issues, scoreBreakdown);

  return (
    <label className="seo-field-editor__field">
      <span className="seo-field-editor__label">
        {label}
        <SeoFieldStatusBadge
          field={field}
          value={value}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
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
  mediaImages = [],
  onChange,
  onImageAltChange,
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
          onChange={onChange}
        />
        <FieldRow
          label="Handle"
          field="handle"
          value={String(values.handle ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
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
          onChange={onChange}
        />
        <FieldRow
          label="Meta description"
          field="metaDescription"
          value={String(values.metaDescription ?? "")}
          issues={issues}
          scoreBreakdown={scoreBreakdown}
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
          onChange={onChange}
          multiline
        />
      </Section>

      <Section title="Immagini">
        {entityType === "collection" ? (
          <FieldRow
            label="Alt immagine collection"
            field="imageAlt"
            value={String(values.imageAlt ?? "")}
            issues={issues}
            scoreBreakdown={scoreBreakdown}
            onChange={onChange}
          />
        ) : mediaImages.length === 0 ? (
          <p className="shopify-empty-copy">Nessuna immagine sincronizzata.</p>
        ) : (
          mediaImages.map((img, idx) => (
            <div key={idx} className="seo-images-tab__item">
              {typeof img.url === "string" && (
                <img src={img.url} alt="" className="seo-images-tab__thumb" />
              )}
              <label className="seo-field-editor__field">
                <span className="seo-field-editor__label">
                  Alt text immagine {idx + 1}
                  <SeoFieldStatusBadge
                    field="imageAlt"
                    value={img.altText ?? img.alt}
                    issues={issues}
                    scoreBreakdown={scoreBreakdown}
                  />
                </span>
                <input
                  className="seo-field-editor__input"
                  type="text"
                  value={String(img.altText ?? img.alt ?? "")}
                  onChange={(e) => onImageAltChange?.(idx, e.target.value)}
                />
              </label>
            </div>
          ))
        )}
      </Section>
    </div>
  );
}
