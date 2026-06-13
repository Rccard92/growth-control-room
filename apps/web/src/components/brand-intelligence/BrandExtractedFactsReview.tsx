import { useMemo, useState } from "react";
import type { BrandApplyFactsResponse, BrandExtractedFact, TargetSection } from "@gcr/shared";
import { targetSectionLabel, TARGET_SECTIONS } from "./brandImportUtils";

interface BrandExtractedFactsReviewProps {
  facts: BrandExtractedFact[];
  onApprove: (factId: string) => void;
  onReject: (factId: string) => void;
  onMoveSection: (factId: string, section: TargetSection) => void;
  onEditValue: (factId: string, value: string) => void;
  onApply: (factIds: string[]) => void;
  applying?: boolean;
}

function updateModeLabel(mode?: string): string {
  const map: Record<string, string> = {
    create: "Nuovo",
    enrich: "Arricchimento",
    update: "Aggiornamento",
    duplicate_candidate: "Possibile duplicato",
    unknown: "Da classificare",
  };
  return map[mode ?? ""] ?? mode ?? "";
}

function conflictLabel(status?: string): string {
  const map: Record<string, string> = {
    none: "",
    possible_conflict: "Possibile conflitto",
    confirmed_conflict: "Conflitto confermato",
  };
  return map[status ?? ""] ?? "";
}

function formatValue(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.join(", ");
  return JSON.stringify(value, null, 2);
}

export function BrandExtractedFactsReview({
  facts,
  onApprove,
  onReject,
  onMoveSection,
  onEditValue,
  onApply,
  applying,
}: BrandExtractedFactsReviewProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const grouped = useMemo(() => {
    const map = new Map<string, BrandExtractedFact[]>();
    for (const fact of facts) {
      const key = fact.targetSection;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(fact);
    }
    const order = [...TARGET_SECTIONS, "unknown"];
    return order
      .filter((k) => map.has(k))
      .map((k) => ({ section: k, items: map.get(k)! }));
  }, [facts]);

  const approvedIds = facts.filter((f) => f.status === "approved").map((f) => f.id);

  if (facts.length === 0) {
    return <p className="bi-panel__subtitle">Nessun fact estratto. Carica documenti e avvia l&apos;estrazione AI.</p>;
  }

  return (
    <div className="bi-facts-review">
      {grouped.map(({ section, items }) => (
        <div key={section} className="bi-facts-group">
          <h4 className="bi-facts-group__title">{targetSectionLabel(section)}</h4>
          {items.map((fact) => {
            const rowClass = [
              "bi-fact-row",
              `bi-fact-row--${fact.status}`,
              fact.conflictStatus === "possible_conflict" ? "bi-fact-row--conflict" : "",
              fact.status === "needs_review" ? "bi-fact-row--needs_review" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
            <div key={fact.id} className={rowClass}>
              <div className="bi-fact-row__main">
                {(fact.updateMode || fact.conflictStatus) && (
                  <div className="bi-fact-row__badges">
                    {fact.updateMode && (
                      <span className="bi-fact-badge bi-fact-badge--mode">{updateModeLabel(fact.updateMode)}</span>
                    )}
                    {conflictLabel(fact.conflictStatus) && (
                      <span className="bi-fact-badge bi-fact-badge--conflict">
                        {conflictLabel(fact.conflictStatus)}
                      </span>
                    )}
                  </div>
                )}
                {fact.previousValue != null && fact.updateMode === "update" && (
                  <div className="bi-fact-row__diff">
                    <span className="bi-fact-row__diff-label">Valore ufficiale attuale:</span>
                    <span className="bi-fact-row__diff-old">{formatValue(fact.previousValue)}</span>
                    <span className="bi-fact-row__diff-label">Valore proposto:</span>
                  </div>
                )}
                <div className="bi-fact-row__value">
                  {editingId === fact.id ? (
                    <textarea
                      rows={3}
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="bi-fact-row__edit"
                    />
                  ) : (
                    formatValue(fact.extractedValue)
                  )}
                </div>
                <div className="bi-fact-row__meta">
                  {fact.fieldName && <span>Campo: {fact.fieldName} · </span>}
                  Confidence: {Math.round(fact.confidence * 100)}% · {fact.status}
                </div>
                {fact.sourceExcerpt && (
                  <blockquote className="bi-fact-row__excerpt">&ldquo;{fact.sourceExcerpt}&rdquo;</blockquote>
                )}
                {fact.aiReasoning && (
                  <p className="bi-fact-row__reasoning">{fact.aiReasoning}</p>
                )}
              </div>
              <div className="bi-fact-row__actions">
                {editingId === fact.id ? (
                  <>
                    <button
                      type="button"
                      className="gcr-btn gcr-btn--primary gcr-btn--sm"
                      onClick={() => {
                        onEditValue(fact.id, editText);
                        setEditingId(null);
                      }}
                    >
                      Salva
                    </button>
                    <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={() => setEditingId(null)}>
                      Annulla
                    </button>
                  </>
                ) : (
                  <>
                    <button type="button" className="gcr-btn gcr-btn--primary gcr-btn--sm" onClick={() => onApprove(fact.id)}>
                      Approva
                    </button>
                    <button
                      type="button"
                      className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                      onClick={() => {
                        setEditingId(fact.id);
                        setEditText(formatValue(fact.extractedValue));
                      }}
                    >
                      Modifica
                    </button>
                    <select
                      className="bi-fact-row__select"
                      value={fact.targetSection}
                      onChange={(e) => onMoveSection(fact.id, e.target.value as TargetSection)}
                    >
                      {TARGET_SECTIONS.map((s) => (
                        <option key={s} value={s}>
                          {targetSectionLabel(s)}
                        </option>
                      ))}
                      <option value="unknown">Da classificare</option>
                    </select>
                    <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={() => onReject(fact.id)}>
                      Rifiuta
                    </button>
                  </>
                )}
              </div>
            </div>
            );
          })}
        </div>
      ))}

      <div className="bi-save-bar">
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={applying || approvedIds.length === 0}
          onClick={() => onApply(approvedIds)}
        >
          {applying ? "Applicazione…" : `Applica ${approvedIds.length} facts approvati alla Brand Intelligence`}
        </button>
      </div>
    </div>
  );
}

interface BrandImportApplySummaryProps {
  result: BrandApplyFactsResponse;
}

export function BrandImportApplySummary({ result }: BrandImportApplySummaryProps) {
  return (
    <div className="bi-apply-summary gcr-card">
      <h4 className="bi-panel__title">Riepilogo applicazione</h4>
      <p className="bi-panel__subtitle">
        {result.counts.saved} informazioni salvate, {result.counts.needsReview} da revisionare,{" "}
        {result.counts.rejected} rifiutate.
      </p>
      {result.saved.length > 0 && (
        <ul className="bi-recommendations">
          {result.saved.map((item) => (
            <li key={item.factId}>{item.message}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
