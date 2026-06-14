import type { SeoScoreBreakdown } from "@gcr/shared";
import { SeoFieldStatusBadge, fieldStatusNote } from "./SeoFieldStatusBadge";
import type { FieldStateMap } from "./seoFieldState";
import type { SeoFormValues } from "./seoFormValues";
import { getUniqueFieldHelperText } from "./seoFormValues";
import {
  applicabilityNote,
  resolveImageAltFieldKey,
} from "./seoAltBatch";

interface SeoImagesEditorProps {
  entityType: "product" | "collection";
  values: SeoFormValues;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  mediaImages?: Record<string, unknown>[];
  collectionImage?: Record<string, unknown> | null;
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
  collectionImage = null,
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
  const collectionApplicable = collectionImage?.shopifyApplicable !== false;

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
              shopifyApplicable={collectionImage?.shopifyApplicable !== false && collectionApplicable}
              applicabilityNote={
                collectionImage?.shopifyApplicable === false
                  ? "Questa immagine non ha un riferimento Shopify aggiornabile"
                  : undefined
              }
            />
            <span className="seo-field-editor__actions">
              {openaiConfigured && onGenerateField && collectionImage?.shopifyApplicable !== false && (
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
              {fieldStateMap?.imageAlt?.source === "ai" &&
                !fieldStateMap.imageAlt.accepted &&
                fieldStateMap.imageAlt.dirty &&
                onAcceptField && (
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                    onClick={(e) => {
                      e.preventDefault();
                      onAcceptField("imageAlt");
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
            value={String(values.imageAlt ?? "")}
            disabled={fieldStateMap?.imageAlt?.generating}
            onChange={(e) => onChange("imageAlt", e.target.value)}
          />
          {(() => {
            const fs = fieldStateMap?.imageAlt;
            const helperText = getUniqueFieldHelperText(
              fs,
              fieldStatusNote(
                "imageAlt",
                values.imageAlt,
                issues,
                scoreBreakdown,
                undefined,
                fs,
                {
                  shopifyApplicable: collectionImage?.shopifyApplicable !== false,
                  applicabilityNote:
                    collectionImage?.shopifyApplicable === false
                      ? "Questa immagine non ha un riferimento Shopify aggiornabile"
                      : undefined,
                },
              ),
            );
            return helperText ? (
              <span className="seo-field-editor__note">{helperText}</span>
            ) : null;
          })()}
        </label>
      ) : mediaImages.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna immagine sincronizzata.</p>
      ) : (
        mediaImages.map((img, idx) => {
          const { fieldKey: fk, imageId, applicable } = resolveImageAltFieldKey(img, idx);
          const fs = fieldStateMap?.[fk];
          const altVal = String(img.altText ?? img.alt ?? "");
          const note = applicabilityNote(img);
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
                    shopifyApplicable={applicable}
                    perImageMode
                    applicabilityNote={note}
                  />
                  <span className="seo-field-editor__actions">
                    {openaiConfigured && onGenerateField && applicable && imageId && (
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
                {(() => {
                  const helperText = getUniqueFieldHelperText(
                    fs,
                    fieldStatusNote("imageAlt", altVal, issues, scoreBreakdown, undefined, fs, {
                      shopifyApplicable: applicable,
                      perImageMode: true,
                      applicabilityNote: note,
                    }),
                  );
                  return helperText ? (
                    <span className="seo-field-editor__note">{helperText}</span>
                  ) : null;
                })()}
              </label>
            </div>
          );
        })
      )}
    </div>
  );
}
