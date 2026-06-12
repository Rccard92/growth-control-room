import { useMemo, useState } from "react";
import type { SeoCollectionListItem, SeoProductListItem } from "@gcr/shared";
import { ShowMoreToggle } from "../../shopify/ShowMoreToggle";
import { CONTENT_SEO_ROW_LIMIT, sliceContentRows } from "../../../lib/content-seo-blocks";
import { SeoScoreBadge } from "./SeoScoreBadge";

export type EntityFilter =
  | "all"
  | "low_score"
  | "critical"
  | "no_meta"
  | "no_alt"
  | "with_proposal";

interface EntitySeoTableProps {
  items: SeoProductListItem[] | SeoCollectionListItem[];
  mode: "product" | "collection";
  filter: EntityFilter;
  onFilterChange: (f: EntityFilter) => void;
  onGenerate: (id: string) => void;
  onDetails: (id: string) => void;
  generateLoadingId?: string | null;
  openaiConfigured: boolean;
}

function matchesFilter(
  item: SeoProductListItem | SeoCollectionListItem,
  filter: EntityFilter,
): boolean {
  if (filter === "all") return true;
  if (filter === "low_score") return (item.score ?? 100) < 60;
  if (filter === "critical") return item.severity === "critical";
  if (filter === "with_proposal") return item.hasProposal;
  if (filter === "no_meta") {
    return item.mainIssues.some(
      (i) => i.toLowerCase().includes("meta") || i.toLowerCase().includes("seo title"),
    );
  }
  if (filter === "no_alt") {
    return item.mainIssues.some((i) => i.toLowerCase().includes("alt"));
  }
  return true;
}

export function EntitySeoTable({
  items,
  mode,
  filter,
  onFilterChange,
  onGenerate,
  onDetails,
  generateLoadingId,
  openaiConfigured,
}: EntitySeoTableProps) {
  const [expanded, setExpanded] = useState(false);

  const filtered = useMemo(
    () => items.filter((item) => matchesFilter(item, filter)),
    [items, filter],
  );
  const visible = sliceContentRows(filtered, expanded, CONTENT_SEO_ROW_LIMIT);

  const filters: { id: EntityFilter; label: string }[] = [
    { id: "all", label: "Tutti" },
    { id: "low_score", label: "Score basso" },
    { id: "critical", label: "Critici" },
    { id: "no_meta", label: "Senza meta" },
    { id: "no_alt", label: "Senza alt" },
    { id: "with_proposal", label: "Con proposta" },
  ];

  return (
    <div className="seo-entity-table">
      <div className="seo-entity-table__filters">
        {filters.map((f) => (
          <button
            key={f.id}
            type="button"
            className={`seo-filter-chip ${filter === f.id ? "seo-filter-chip--active" : ""}`}
            onClick={() => onFilterChange(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="shopify-empty-copy">Nessun elemento per questo filtro. Esegui analisi dopo sync.</p>
      ) : (
        <>
          <div className="seo-entity-table__head">
            <span>Titolo</span>
            <span>Score</span>
            <span>Problemi</span>
            {mode === "product" && <span>Vendite / Stock</span>}
            {mode === "collection" && <span>Prodotti</span>}
            <span>Azioni</span>
          </div>
          {visible.map((item) => (
            <div key={item.id} className="seo-entity-table__row">
              <div>
                <strong>{item.title}</strong>
                {item.handle && (
                  <span className="seo-entity-table__handle">/{item.handle}</span>
                )}
              </div>
              <SeoScoreBadge score={item.score} severity={item.severity} />
              <ul className="seo-entity-table__issues">
                {item.mainIssues.slice(0, 2).map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
                {item.mainIssues.length === 0 && <li>—</li>}
              </ul>
              {mode === "product" && "quantitySold" in item && (
                <span>
                  {item.quantitySold} / {item.stock ?? "—"}
                </span>
              )}
              {mode === "collection" && "productsCount" in item && (
                <span>{item.productsCount ?? "—"}</span>
              )}
              <div className="seo-entity-table__actions">
                <button
                  type="button"
                  className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                  onClick={() => onDetails(item.id)}
                >
                  Dettagli
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                  disabled={!openaiConfigured || generateLoadingId === item.id}
                  title={
                    openaiConfigured
                      ? undefined
                      : "AI non configurata. Aggiungi OPENAI_API_KEY per generare proposte automatiche."
                  }
                  onClick={() => onGenerate(item.id)}
                >
                  {generateLoadingId === item.id ? "…" : "Genera proposta"}
                </button>
              </div>
            </div>
          ))}
          <ShowMoreToggle
            total={filtered.length}
            limit={CONTENT_SEO_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((v) => !v)}
          />
        </>
      )}
    </div>
  );
}
