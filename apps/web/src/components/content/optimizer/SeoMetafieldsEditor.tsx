import type { SeoProductMetafieldItem } from "@gcr/shared";
import type { FieldStateMap } from "./seoFieldState";
import { metafieldFieldKey } from "./seoFieldState";

interface SeoMetafieldsEditorProps {
  metafields: SeoProductMetafieldItem[];
  fieldStateMap?: FieldStateMap;
  openaiConfigured?: boolean;
  syncLoading?: boolean;
  onMetafieldChange: (metafieldId: string, value: string) => void;
  onGenerateMetafield?: (metafieldId: string) => void;
  onRestoreField?: (fieldKey: string) => void;
  onAcceptField?: (fieldKey: string) => void;
  onSyncMetafields?: () => void;
}

export function SeoMetafieldsEditor({
  metafields,
  fieldStateMap,
  openaiConfigured,
  syncLoading,
  onMetafieldChange,
  onGenerateMetafield,
  onRestoreField,
  onAcceptField,
  onSyncMetafields,
}: SeoMetafieldsEditorProps) {
  if (metafields.length === 0) {
    return (
      <div className="seo-metafields-editor">
        <p className="shopify-empty-copy">Questo prodotto non ha metafield sincronizzati.</p>
        {onSyncMetafields && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            disabled={syncLoading}
            onClick={onSyncMetafields}
          >
            {syncLoading ? "Sincronizzazione…" : "Sincronizza metafield prodotto"}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="seo-metafields-editor">
      {onSyncMetafields && (
        <div className="seo-metafields-editor__toolbar">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            disabled={syncLoading}
            onClick={onSyncMetafields}
          >
            {syncLoading ? "Sincronizzazione…" : "Sincronizza metafield prodotto"}
          </button>
        </div>
      )}
      {metafields.map((mf) => {
        const fk = metafieldFieldKey(mf.id);
        const fs = fieldStateMap?.[fk];
        const value = fs?.value ?? mf.value ?? "";
        const showRestore = fs?.dirty && fs.value !== fs.originalValue;
        const showAccept = fs?.source === "ai" && !fs.accepted && fs.dirty;
        const multiline =
          mf.type === "multi_line_text_field" ||
          mf.type === "rich_text_field" ||
          value.length > 120;

        return (
          <div key={mf.id} className="seo-metafield-item">
            <div className="seo-metafield-item__header">
              <strong>
                {mf.namespace}.{mf.key}
              </strong>
              <span className="seo-metafield-item__type">{mf.type}</span>
              {!mf.editable && (
                <span className="seo-metafield-item__badge">Solo lettura</span>
              )}
            </div>
            {mf.definitionName && (
              <p className="seo-metafield-item__definition">{mf.definitionName}</p>
            )}
            {mf.definitionDescription && (
              <p className="seo-metafield-item__description">{mf.definitionDescription}</p>
            )}
            <label className="seo-field-editor__field">
              <span className="seo-field-editor__label">
                Valore
                <span className="seo-field-editor__actions">
                  {mf.aiGeneratable && openaiConfigured && onGenerateMetafield && (
                    <button
                      type="button"
                      className="gcr-btn gcr-btn--secondary gcr-btn--sm seo-field-ai-btn"
                      title="Genera solo questo metafield"
                      disabled={fs?.generating}
                      onClick={(e) => {
                        e.preventDefault();
                        onGenerateMetafield(mf.id);
                      }}
                    >
                      {fs?.generating ? "…" : "✦ AI"}
                    </button>
                  )}
                  {showRestore && onRestoreField && (
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
                  {showAccept && onAcceptField && (
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
              {mf.editable ? (
                multiline ? (
                  <textarea
                    className="seo-field-editor__input"
                    rows={4}
                    value={value}
                    disabled={fs?.generating}
                    onChange={(e) => onMetafieldChange(mf.id, e.target.value)}
                  />
                ) : (
                  <input
                    className="seo-field-editor__input"
                    type="text"
                    value={value}
                    disabled={fs?.generating}
                    onChange={(e) => onMetafieldChange(mf.id, e.target.value)}
                  />
                )
              ) : (
                <div className="seo-field-editor__readonly-value">{value || "—"}</div>
              )}
              {fs?.reasoning && (
                <span className="seo-field-editor__note">{fs.reasoning}</span>
              )}
            </label>
          </div>
        );
      })}
    </div>
  );
}
