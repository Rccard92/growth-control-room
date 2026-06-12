import { SeoMissingFieldBadge } from "./SeoMissingFieldBadge";

interface SeoFieldEditorProps {
  entityType: "product" | "collection";
  values: Record<string, unknown>;
  issues?: Record<string, unknown>[] | null;
  onChange: (key: string, value: unknown) => void;
}

function TextInput({
  label,
  fieldKey,
  value,
  issues,
  onChange,
  multiline,
}: {
  label: string;
  fieldKey: string;
  value: string;
  issues?: Record<string, unknown>[] | null;
  onChange: (key: string, value: string) => void;
  multiline?: boolean;
}) {
  const badgeField =
    fieldKey === "seo_title"
      ? "seoTitle"
      : fieldKey === "meta_description"
        ? "metaDescription"
        : fieldKey === "description_html"
          ? "description"
          : fieldKey === "product_title" || fieldKey === "collection_title"
            ? "title"
            : fieldKey;

  return (
    <label className="seo-field-editor__field">
      <span className="seo-field-editor__label">
        {label}
        <SeoMissingFieldBadge field={badgeField} issues={issues} />
      </span>
      {multiline ? (
        <textarea
          className="seo-field-editor__input"
          rows={4}
          value={value}
          onChange={(e) => onChange(fieldKey, e.target.value)}
        />
      ) : (
        <input
          className="seo-field-editor__input"
          type="text"
          value={value}
          onChange={(e) => onChange(fieldKey, e.target.value)}
        />
      )}
    </label>
  );
}

export function SeoFieldEditor({
  entityType,
  values,
  issues,
  onChange,
}: SeoFieldEditorProps) {
  const titleKey = entityType === "product" ? "product_title" : "collection_title";
  const tags = Array.isArray(values.tags) ? (values.tags as string[]).join(", ") : "";

  return (
    <div className="seo-field-editor">
      <TextInput
        label={entityType === "product" ? "Titolo prodotto" : "Titolo collection"}
        fieldKey={titleKey}
        value={String(values[titleKey] ?? "")}
        issues={issues}
        onChange={onChange}
      />
      <TextInput
        label="Handle"
        fieldKey="handle"
        value={String(values.handle ?? "")}
        issues={issues}
        onChange={onChange}
      />
      <TextInput
        label="SEO title"
        fieldKey="seo_title"
        value={String(values.seo_title ?? "")}
        issues={issues}
        onChange={onChange}
      />
      <TextInput
        label="Meta description"
        fieldKey="meta_description"
        value={String(values.meta_description ?? "")}
        issues={issues}
        onChange={onChange}
        multiline
      />
      <TextInput
        label="Descrizione (HTML)"
        fieldKey="description_html"
        value={String(values.description_html ?? "")}
        issues={issues}
        onChange={onChange}
        multiline
      />
      {entityType === "product" && (
        <TextInput
          label="Tag (separati da virgola)"
          fieldKey="tags"
          value={tags}
          issues={issues}
          onChange={(key, val) =>
            onChange(
              key,
              val
                .split(",")
                .map((t) => t.trim())
                .filter(Boolean),
            )
          }
        />
      )}
      {entityType === "collection" && (
        <TextInput
          label="Alt immagine collection"
          fieldKey="image_alt"
          value={String(values.image_alt ?? "")}
          issues={issues}
          onChange={onChange}
        />
      )}
    </div>
  );
}
