import { useEffect, useState } from "react";
import type {
  ContentSeoEditorialItem,
  ContentSeoEditorialObjective,
  ContentSeoEditorialStatus,
} from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
  CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS,
  CONTENT_SEO_EDITORIAL_STATUS_LABELS,
} from "@gcr/shared";
import { EditorialStatusBadge } from "./EditorialStatusLegend";
import {
  useDeleteEditorialItem,
  useUpdateEditorialItem,
} from "../../../hooks/useContentSeoEditorial";

interface EditorialItemDrawerProps {
  open: boolean;
  item: ContentSeoEditorialItem | null;
  projectId: string;
  onClose: () => void;
}

export function EditorialItemDrawer({
  open,
  item,
  projectId,
  onClose,
}: EditorialItemDrawerProps) {
  const updateMutation = useUpdateEditorialItem(projectId);
  const deleteMutation = useDeleteEditorialItem(projectId);

  const [title, setTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [status, setStatus] = useState<ContentSeoEditorialStatus>("idea");
  const [objective, setObjective] = useState<ContentSeoEditorialObjective | "">("");
  const [primaryKeyword, setPrimaryKeyword] = useState("");
  const [secondaryKeywords, setSecondaryKeywords] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!item) return;
    setTitle(item.title);
    setPlannedDate(item.plannedDate.slice(0, 10));
    setStatus(item.status);
    setObjective(item.objective ?? "");
    setPrimaryKeyword(item.primaryKeyword ?? "");
    setSecondaryKeywords((item.secondaryKeywords ?? []).join(", "));
    setNotes(item.notes ?? "");
    setError(null);
  }, [item]);

  if (!open || !item) return null;

  async function handleSave() {
    if (!item) return;
    setError(null);
    try {
      await updateMutation.mutateAsync({
        itemId: item.id,
        data: {
          title: title.trim(),
          plannedDate,
          status,
          objective: objective || null,
          primaryKeyword: primaryKeyword.trim() || null,
          secondaryKeywords: secondaryKeywords
            .split(",")
            .map((k) => k.trim())
            .filter(Boolean),
          notes: notes.trim() || null,
        },
      });
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio.");
    }
  }

  async function handleDelete() {
    if (!item) return;
    if (!window.confirm("Eliminare questo item dal calendario?")) return;
    setError(null);
    try {
      await deleteMutation.mutateAsync(item.id);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante l'eliminazione.");
    }
  }

  const hasBrief = Boolean(item.briefPayload && Object.keys(item.briefPayload).length > 0);

  return (
    <div className="seo-drawer-backdrop" onClick={onClose} role="presentation">
      <aside
        className="seo-drawer gcr-card editorial-drawer"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Dettaglio item editoriale"
      >
        <header className="seo-drawer__header">
          <div>
            <p className="gcr-card__label">Item editoriale</p>
            <h3>{item.title}</h3>
            <p className="editorial-drawer__type">
              {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType]}
            </p>
            <EditorialStatusBadge status={item.status} />
          </div>
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
            Chiudi
          </button>
        </header>

        {error && <div className="gcr-alert gcr-alert--error">{error}</div>}

        <section className="seo-drawer__section">
          <label className="gcr-field">
            <span className="gcr-field__label">Titolo</span>
            <input
              className="gcr-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Data pianificata</span>
            <input
              type="date"
              className="gcr-input"
              value={plannedDate}
              onChange={(e) => setPlannedDate(e.target.value)}
            />
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Stato</span>
            <select
              className="gcr-input"
              value={status}
              onChange={(e) => setStatus(e.target.value as ContentSeoEditorialStatus)}
            >
              {Object.entries(CONTENT_SEO_EDITORIAL_STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Obiettivo</span>
            <select
              className="gcr-input"
              value={objective}
              onChange={(e) =>
                setObjective(e.target.value as ContentSeoEditorialObjective | "")
              }
            >
              <option value="">—</option>
              {Object.entries(CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Keyword principale</span>
            <input
              className="gcr-input"
              value={primaryKeyword}
              onChange={(e) => setPrimaryKeyword(e.target.value)}
            />
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Keyword secondarie (separate da virgola)</span>
            <input
              className="gcr-input"
              value={secondaryKeywords}
              onChange={(e) => setSecondaryKeywords(e.target.value)}
            />
          </label>

          <label className="gcr-field">
            <span className="gcr-field__label">Note</span>
            <textarea
              className="gcr-input"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>

          {item.linkedShopifyProductTitle && (
            <p className="editorial-drawer__linked">
              Prodotto collegato: <strong>{item.linkedShopifyProductTitle}</strong>
            </p>
          )}
        </section>

        <section className="seo-drawer__section editorial-drawer__brief">
          <h4>Brief SEO</h4>
          {hasBrief ? (
            <pre className="seo-drawer__json">{JSON.stringify(item.briefPayload, null, 2)}</pre>
          ) : (
            <p className="gcr-card__description">Brief SEO non ancora generato</p>
          )}
          <button type="button" className="gcr-btn gcr-btn--secondary" disabled title="Prossimo step">
            Genera brief — prossimo step
          </button>
        </section>

        <div className="seo-drawer__actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={updateMutation.isPending || !title.trim()}
            onClick={() => void handleSave()}
          >
            Salva
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--danger"
            disabled={deleteMutation.isPending}
            onClick={() => void handleDelete()}
          >
            Elimina
          </button>
        </div>
      </aside>
    </div>
  );
}
