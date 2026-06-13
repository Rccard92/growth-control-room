import { useMemo, useState } from "react";
import type { SeoProductMetafieldItem } from "@gcr/shared";
import type { FieldStateMap } from "./seoFieldState";
import { metafieldFieldKey } from "./seoFieldState";

type MetafieldFilter = "all" | "empty" | "filled" | "ai" | "readonly";

interface SeoMetafieldsEditorProps {
  metafields: SeoProductMetafieldItem[];
  fieldStateMap?: FieldStateMap;
  openaiConfigured?: boolean;
  syncLoading?: boolean;
  definitionsSyncLoading?: boolean;
  hasDefinitions?: boolean;
  onMetafieldChange: (metafieldId: string, value: string) => void;
  onGenerateMetafield?: (mf: SeoProductMetafieldItem) => void;
  onRestoreField?: (fieldKey: string) => void;
  onAcceptField?: (fieldKey: string) => void;
  onSyncMetafields?: () => void;
  onSyncDefinitions?: () => void;
}

function sortMetafields(items: SeoProductMetafieldItem[]): SeoProductMetafieldItem[] {
  return [...items].sort((a, b) => {
    const rank = (mf: SeoProductMetafieldItem) => {
      if (!mf.editable) return 2;
      if (mf.isEmpty && mf.aiGeneratable) return 0;
      if (mf.isEmpty) return 0;
      return 1;
    };
    const ra = rank(a);
    const rb = rank(b);
    if (ra !== rb) return ra - rb;
    const na = (a.definitionName || a.namespace).toLowerCase();
    const nb = (b.definitionName || b.namespace).toLowerCase();
    return na.localeCompare(nb);
  });
}

function matchesFilter(mf: SeoProductMetafieldItem, filter: MetafieldFilter): boolean {
  if (filter === "all") return true;
  if (filter === "empty") return !!mf.isEmpty;
  if (filter === "filled") return !mf.isEmpty;
  if (filter === "ai") return mf.aiGeneratable;
  if (filter === "readonly") return !mf.editable;
  return true;
}

function statusBadges(
  mf: SeoProductMetafieldItem,
  fs: FieldStateMap[string] | undefined,
): string[] {
  const badges: string[] = [];
  if (!mf.editable) badges.push("Solo lettura");
  else if (mf.isEmpty) badges.push("Vuoto");
  else badges.push("Compilato");
  if (fs?.source === "ai" && fs.dirty && !fs.accepted) badges.push("Proposto da AI");
  if (fs?.source === "ai" && fs.accepted && fs.dirty) badges.push("Accettato");
  if (fs?.riskLevel === "high" || fs?.riskLevel === "medium") badges.push("Da verificare");
  return badges;
}

export function SeoMetafieldsEditor({
  metafields,
  fieldStateMap,
  openaiConfigured,
  syncLoading,
  definitionsSyncLoading,
  hasDefinitions,
  onMetafieldChange,
  onGenerateMetafield,
  onRestoreField,
  onAcceptField,
  onSyncMetafields,
  onSyncDefinitions,
}: SeoMetafieldsEditorProps) {
  const [filter, setFilter] = useState<MetafieldFilter>("all");
  const [showRaw, setShowRaw] = useState<Record<string, boolean>>({});

  const filtered = useMemo(
    () => sortMetafields(metafields.filter((mf) => matchesFilter(mf, filter))),
    [metafields, filter],
  );

  if (metafields.length === 0) {
    return (
      <div className="seo-metafields-editor">
        <p className="shopify-empty-copy">
          {hasDefinitions === false
            ? "Nessuna definizione metafield sincronizzata per questo store."
            : "Questo prodotto non ha metafield sincronizzati."}
        </p>
        <div className="seo-metafields-editor__empty-actions">
          {hasDefinitions === false && onSyncDefinitions && (
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              disabled={definitionsSyncLoading}
              onClick={onSyncDefinitions}
            >
              {definitionsSyncLoading ? "Sincronizzazione…" : "Sincronizza definizioni metafield"}
            </button>
          )}
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
      </div>
    );
  }

  return (
    <div className="seo-metafields-editor">
      <div className="seo-metafields-editor__toolbar">
        <div className="seo-metafields-editor__filters" role="tablist" aria-label="Filtri metafield">
          {(
            [
              ["all", "Tutti"],
              ["empty", "Vuoti"],
              ["filled", "Compilati"],
              ["ai", "AI disponibili"],
              ["readonly", "Solo lettura"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={filter === id}
              className={`seo-metafields-editor__filter${filter === id ? " seo-metafields-editor__filter--active" : ""}`}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="seo-metafields-editor__sync-group">
          {onSyncDefinitions && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              disabled={definitionsSyncLoading}
              onClick={onSyncDefinitions}
            >
              {definitionsSyncLoading ? "…" : "Sincronizza definizioni"}
            </button>
          )}
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
      </div>

      {filtered.length === 0 && (
        <p className="shopify-empty-copy">Nessun metafield corrisponde al filtro selezionato.</p>
      )}

      {filtered.map((mf) => {
        const fk = metafieldFieldKey(mf.id);
        const fs = fieldStateMap?.[fk];
        const displayValue = fs?.value ?? mf.displayValue ?? mf.value ?? "";
        const showRestore = fs?.dirty && fs.value !== fs.originalValue;
        const showAccept = fs?.source === "ai" && !fs.accepted && fs.dirty;
        const multiline =
          mf.type === "multi_line_text_field" ||
          mf.type === "rich_text_field" ||
          displayValue.length > 120;
        const badges = statusBadges(mf, fs);
        const title = mf.definitionName || `${mf.namespace}.${mf.key}`;

        return (
          <div key={mf.id} className="seo-metafield-item">
            <div className="seo-metafield-item__header">
              <div className="seo-metafield-item__titles">
                <strong className="seo-metafield-item__name">{title}</strong>
                <span className="seo-metafield-item__ns-key">
                  {mf.namespace}.{mf.key}
                </span>
              </div>
              <div className="seo-metafield-item__badges">
                <span className="seo-metafield-item__type">{mf.type}</span>
                {badges.map((b) => (
                  <span key={b} className="seo-metafield-item__badge">
                    {b}
                  </span>
                ))}
              </div>
            </div>
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
                        onGenerateMetafield(mf);
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
                    value={displayValue}
                    disabled={fs?.generating}
                    onChange={(e) => onMetafieldChange(mf.id, e.target.value)}
                  />
                ) : (
                  <input
                    className="seo-field-editor__input"
                    type="text"
                    value={displayValue}
                    disabled={fs?.generating}
                    onChange={(e) => onMetafieldChange(mf.id, e.target.value)}
                  />
                )
              ) : (
                <div className="seo-field-editor__readonly-value">{displayValue || "—"}</div>
              )}
              {mf.type === "rich_text_field" && mf.rawValue && (
                <details className="seo-metafield-item__raw">
                  <summary
                    onClick={(e) => {
                      e.preventDefault();
                      setShowRaw((prev) => ({ ...prev, [mf.id]: !prev[mf.id] }));
                    }}
                  >
                    Valore tecnico
                  </summary>
                  {showRaw[mf.id] && (
                    <pre className="seo-metafield-item__raw-pre">{mf.rawValue}</pre>
                  )}
                </details>
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
