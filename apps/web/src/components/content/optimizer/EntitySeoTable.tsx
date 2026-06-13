import { useMemo, useState } from "react";
import { motion } from "framer-motion";
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
  onEdit: (id: string) => void;
  editLoadingId?: string | null;
  emptyMessage?: string;
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
  onEdit,
  editLoadingId,
  emptyMessage,
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
        <p className="shopify-empty-copy">
          {items.length === 0 && emptyMessage
            ? emptyMessage
            : "Nessun elemento per questo filtro. Esegui analisi dopo sync."}
        </p>
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
          {visible.map((item) => {
            const titleLine = item.title;
            const handleLine = item.handle ? `/${item.handle}` : "";
            const titleTooltip = handleLine ? `${titleLine} ${handleLine}` : titleLine;

            return (
              <motion.div
                key={item.id}
                className="seo-entity-table__row"
                whileHover={{ backgroundColor: "rgba(255, 255, 255, 0.03)" }}
                transition={{ duration: 0.15 }}
              >
                <div className="seo-entity-table__title-cell" title={titleTooltip}>
                  <strong className="seo-entity-table__title-text">{titleLine}</strong>
                  {item.handle && (
                    <span className="seo-entity-table__handle">/{item.handle}</span>
                  )}
                </div>
                <SeoScoreBadge score={item.score} severity={item.severity} />
                <ul className="seo-entity-table__issues">
                  {item.mainIssues.slice(0, 2).map((issue) => (
                    <li key={issue} title={issue}>
                      {issue}
                    </li>
                  ))}
                  {item.mainIssues.length === 0 && <li>—</li>}
                </ul>
                {mode === "product" && "quantitySold" in item && (
                  <span className="seo-entity-table__metric">
                    {item.quantitySold} / {item.stock ?? "—"}
                  </span>
                )}
                {mode === "collection" && "productsCount" in item && (
                  <span className="seo-entity-table__metric">{item.productsCount ?? "—"}</span>
                )}
                <div className="seo-entity-table__actions">
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--primary gcr-btn--sm"
                    disabled={editLoadingId === item.id}
                    onClick={() => onEdit(item.id)}
                  >
                    {editLoadingId === item.id ? "…" : "Modifica"}
                  </button>
                </div>
              </motion.div>
            );
          })}
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
