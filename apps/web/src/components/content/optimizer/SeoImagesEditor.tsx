import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge } from "./SeoFieldStatusBadge";
import type { SeoFormValues } from "./seoFormValues";

interface SeoImagesEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  mediaImages?: Record<string, unknown>[];
  aiFilledFields?: Set<string>;
  onChange: (key: string, value: unknown) => void;
  onImageAltChange?: (index: number, alt: string) => void;
}

export function SeoImagesEditor({
  entityType,
  values,
  issues,
  scoreBreakdown,
  mediaImages = [],
  aiFilledFields,
  onChange,
  onImageAltChange,
}: SeoImagesEditorProps) {
  return (
    <div className="seo-field-editor seo-images-editor">
      {entityType === "collection" ? (
        <label className="seo-field-editor__field">
          <span className="seo-field-editor__label">
            Alt immagine collection
            <SeoFieldStatusBadge
              field="imageAlt"
              value={values.imageAlt}
              issues={issues}
              scoreBreakdown={scoreBreakdown}
              aiFilledFields={aiFilledFields}
            />
          </span>
          <input
            className="seo-field-editor__input"
            type="text"
            value={String(values.imageAlt ?? "")}
            onChange={(e) => onChange("imageAlt", e.target.value)}
          />
        </label>
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
                  aiFilledFields={aiFilledFields}
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
    </div>
  );
}
