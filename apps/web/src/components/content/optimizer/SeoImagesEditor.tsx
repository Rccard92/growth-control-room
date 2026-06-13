import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge } from "./SeoFieldStatusBadge";
import type { FieldStateMap } from "./seoFieldState";
import { imageAltFieldKey } from "./seoFieldState";
import type { SeoFormValues } from "./seoFormValues";

interface SeoImagesEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  mediaImages?: Record<string, unknown>[];
  fieldStateMap?: FieldStateMap;
  openaiConfigured?: boolean;
  missingAltCount?: number;
  batchAltLoading?: boolean;
  onChange: (key: string, value: unknown) => void;
  onImageAltChange?: (index: number, alt: string) => void;
  onGenerateField?: (field: "imageAlt", imageId?: string) => void;
  onGenerateMissingAlts?: () => void;
  onRestoreField?: (field: string) => void;
  onAcceptField?: (field: string) => void;
}

export function SeoImagesEditor({
  entityType,
  values,
  issues,
  scoreBreakdown,
  mediaImages = [],
  fieldStateMap,
  openaiConfigured,
  missingAltCount = 0,
  batchAltLoading = false,
  onChange,
  onImageAltChange,
  onGenerateField,
  onGenerateMissingAlts,
  onRestoreField,
  onAcceptField,
}: SeoImagesEditorProps) {
  const allHaveAlt = entityType === "product" && mediaImages.length > 0 && missingAltCount === 0;

  return (
    <div className="seo-field-editor seo-images-editor">
      {entityType === "product" && mediaImages.length > 0 && openaiConfigured && onGenerateMissingAlts && (
        <div className="seo-images-editor__toolbar">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            disabled={allHaveAlt || batchAltLoading}
            title={
              allHaveAlt ? "Tutte le immagini hanno già un ALT text." : undefined
            }
            onClick={onGenerateMissingAlts}
          >
            {batchAltLoading ? "Generazione ALT…" : "Genera ALT mancanti"}
          </button>
          {missingAltCount > 0 && !batchAltLoading && (
            <span className="seo-images-editor__hint">
              {missingAltCount} {missingAltCount === 1 ? "immagine senza ALT" : "immagini senza ALT"}
            </span>
          )}
        </div>
      )}

      {entityType === "collection" ? (
        <label className="seo-field-editor__field">
          <span className="seo-field-editor__label">
            Alt immagine collection
            <SeoFieldStatusBadge
              field="imageAlt"
              value={values.imageAlt}
              issues={issues}
              scoreBreakdown={scoreBreakdown}
              fieldState={fieldStateMap?.imageAlt}
            />
            <span className="seo-field-editor__actions">
              {openaiConfigured && onGenerateField && (
                <button
                  type="button"
                  className="gcr-btn gcr-btn--secondary gcr-btn--sm seo-field-ai-btn"
                  title="Genera solo questo campo"
                  disabled={fieldStateMap?.imageAlt?.generating}
                  onClick={(e) => {
                    e.preventDefault();
                    onGenerateField("imageAlt");
                  }}
                >
                  {fieldStateMap?.imageAlt?.generating ? "…" : "✦ AI"}
                </button>
              )}
              {fieldStateMap?.imageAlt?.dirty &&
                fieldStateMap.imageAlt.value !== fieldStateMap.imageAlt.originalValue &&
                onRestoreField && (
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                    onClick={(e) => {
                      e.preventDefault();
                      onRestoreField("imageAlt");
                    }}
                  >
                    Ripristina
                  </button>
                )}
            </span>
          </span>
          <input
            className="seo-field-editor__input"
            type="text"
            value={String(values.imageAlt ?? "")}
            disabled={fieldStateMap?.imageAlt?.generating}
            onChange={(e) => onChange("imageAlt", e.target.value)}
          />
          {fieldStateMap?.imageAlt?.reasoning && (
            <span className="seo-field-editor__note">{fieldStateMap.imageAlt.reasoning}</span>
          )}
        </label>
      ) : mediaImages.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna immagine sincronizzata.</p>
      ) : (
        mediaImages.map((img, idx) => {
          const imageId = String(img.id ?? idx);
          const fk = imageAltFieldKey(imageId);
          const fs = fieldStateMap?.[fk];
          const altVal = String(img.altText ?? img.alt ?? "");
          return (
            <div key={fk} className="seo-images-tab__item">
              {typeof img.url === "string" && (
                <img src={img.url} alt="" className="seo-images-tab__thumb" />
              )}
              <label className="seo-field-editor__field">
                <span className="seo-field-editor__label">
                  Alt text immagine {idx + 1}
                  <SeoFieldStatusBadge
                    field="imageAlt"
                    value={altVal}
                    issues={issues}
                    scoreBreakdown={scoreBreakdown}
                    fieldState={fs}
                  />
                  <span className="seo-field-editor__actions">
                    {openaiConfigured && onGenerateField && (
                      <button
                        type="button"
                        className="gcr-btn gcr-btn--secondary gcr-btn--sm seo-field-ai-btn"
                        title="Genera solo questo campo"
                        disabled={fs?.generating}
                        onClick={(e) => {
                          e.preventDefault();
                          onGenerateField("imageAlt", imageId);
                        }}
                      >
                        {fs?.generating ? "…" : "✦ AI"}
                      </button>
                    )}
                    {fs?.dirty && fs.value !== fs.originalValue && onRestoreField && (
                      <button
                        type="button"
                        className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                        onClick={(e) => {
                          e.preventDefault();
                          onRestoreField(fk);
                        }}
                      >
                        Ripristina
                      </button>
                    )}
                    {fs?.source === "ai" && !fs.accepted && fs.dirty && onAcceptField && (
                      <button
                        type="button"
                        className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                        onClick={(e) => {
                          e.preventDefault();
                          onAcceptField(fk);
                        }}
                      >
                        Accetta
                      </button>
                    )}
                  </span>
                </span>
                <input
                  className="seo-field-editor__input"
                  type="text"
                  value={altVal}
                  disabled={fs?.generating}
                  onChange={(e) => onImageAltChange?.(idx, e.target.value)}
                />
                {fs?.reasoning && (
                  <span className="seo-field-editor__note">{fs.reasoning}</span>
                )}
              </label>
            </div>
          );
        })
      )}
    </div>
  );
}
