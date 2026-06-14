import { useEffect, useMemo, useState } from "react";
import type {
  ContentSeoEditorialItem,
  ContentSeoEditorialObjective,
  ContentSeoEditorialStatus,
  EditorialBriefPayload,
} from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
  CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS,
  CONTENT_SEO_EDITORIAL_STATUS_LABELS,
} from "@gcr/shared";
import { EditorialBriefEditor } from "./EditorialBriefEditor";
import {
  hasEditorialBrief,
  parseEditorialBriefPayload,
} from "./editorial-brief-utils";
import { EditorialStatusBadge } from "./EditorialStatusLegend";
import { AppSelect } from "../../ui/AppSelect";
import {
  useDeleteEditorialItem,
  useGenerateEditorialBrief,
  useUpdateEditorialBrief,
  useUpdateEditorialItem,
} from "../../../hooks/useContentSeoEditorial";

interface EditorialItemDrawerProps {
  open: boolean;
  item: ContentSeoEditorialItem | null;
  projectId: string;
  onClose: () => void;
  onItemUpdated?: (item: ContentSeoEditorialItem) => void;
}

export function EditorialItemDrawer({
  open,
  item,
  projectId,
  onClose,
  onItemUpdated,
}: EditorialItemDrawerProps) {
  const updateMutation = useUpdateEditorialItem(projectId);
  const deleteMutation = useDeleteEditorialItem(projectId);
  const generateBriefMutation = useGenerateEditorialBrief(projectId);
  const updateBriefMutation = useUpdateEditorialBrief(projectId);

  const [title, setTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [status, setStatus] = useState<ContentSeoEditorialStatus>("idea");
  const [objective, setObjective] = useState<ContentSeoEditorialObjective | "">("");
  const [primaryKeyword, setPrimaryKeyword] = useState("");
  const [secondaryKeywords, setSecondaryKeywords] = useState("");
  const [notes, setNotes] = useState("");
  const [brief, setBrief] = useState<EditorialBriefPayload | null>(null);
  const [savedBriefSnapshot, setSavedBriefSnapshot] = useState("");
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
    const parsed = parseEditorialBriefPayload(item.briefPayload ?? null);
    setBrief(hasEditorialBrief(item.briefPayload ?? null) ? parsed : null);
    setSavedBriefSnapshot(JSON.stringify(parsed));
    setError(null);
  }, [item]);

  const briefDirty = useMemo(() => {
    if (!brief) return false;
    return JSON.stringify(brief) !== savedBriefSnapshot;
  }, [brief, savedBriefSnapshot]);

  if (!open || !item) return null;

  const currentItem = item;
  const hasBrief = Boolean(brief);

  const statusOptions = Object.entries(CONTENT_SEO_EDITORIAL_STATUS_LABELS).map(
    ([value, label]) => ({ value, label }),
  );
  const objectiveOptions = [
    { value: "", label: "—" },
    ...Object.entries(CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS).map(([value, label]) => ({
      value,
      label,
    })),
  ];

  function syncItem(updated: ContentSeoEditorialItem) {
    onItemUpdated?.(updated);
    setStatus(updated.status);
    const parsed = parseEditorialBriefPayload(updated.briefPayload ?? null);
    if (hasEditorialBrief(updated.briefPayload ?? null)) {
      setBrief(parsed);
      setSavedBriefSnapshot(JSON.stringify(parsed));
    }
  }

  async function handleSaveMetadata() {
    setError(null);
    try {
      const updated = await updateMutation.mutateAsync({
        itemId: currentItem.id,
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
      syncItem(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio.");
    }
  }

  async function handleDelete() {
    if (!window.confirm("Eliminare questo item dal calendario?")) return;
    setError(null);
    try {
      await deleteMutation.mutateAsync(currentItem.id);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante l'eliminazione.");
    }
  }

  async function handleGenerateBrief() {
    if (
      hasBrief &&
      briefDirty &&
      !window.confirm(
        "Rigenerando perderai le modifiche non salvate. Continuare?",
      )
    ) {
      return;
    }
    setError(null);
    try {
      const updated = await generateBriefMutation.mutateAsync(currentItem.id);
      syncItem(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante la generazione del brief.");
    }
  }

  async function handleSaveBrief(approve = false) {
    if (!brief) return;
    setError(null);
    try {
      const updated = await updateBriefMutation.mutateAsync({
        itemId: currentItem.id,
        data: {
          briefPayload: brief,
          status: approve ? "brief_approved" : undefined,
        },
      });
      syncItem(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante il salvataggio del brief.");
    }
  }

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
            <h3>{currentItem.title}</h3>
            <p className="editorial-drawer__type">
              {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[currentItem.contentType]}
            </p>
            <EditorialStatusBadge status={currentItem.status} />
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

          <AppSelect
            label="Stato"
            value={status}
            options={statusOptions}
            onChange={(v) => setStatus(v as ContentSeoEditorialStatus)}
          />

          <AppSelect
            label="Obiettivo"
            value={objective}
            options={objectiveOptions}
            onChange={(v) => setObjective(v as ContentSeoEditorialObjective | "")}
          />

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

          {currentItem.linkedShopifyProductTitle && (
            <p className="editorial-drawer__linked">
              Prodotto collegato: <strong>{currentItem.linkedShopifyProductTitle}</strong>
            </p>
          )}
        </section>

        <section className="seo-drawer__section editorial-drawer__brief">
          <h4>Brief SEO</h4>
          {hasBrief ? (
            <EditorialBriefEditor value={brief!} onChange={setBrief} />
          ) : (
            <p className="gcr-card__description">Brief SEO non ancora generato</p>
          )}

          <div className="editorial-drawer__brief-actions">
            {!hasBrief && (
              <button
                type="button"
                className="gcr-btn gcr-btn--primary"
                disabled={generateBriefMutation.isPending}
                onClick={() => void handleGenerateBrief()}
              >
                {generateBriefMutation.isPending ? "Generazione…" : "Genera brief"}
              </button>
            )}
            {hasBrief && (
              <>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--secondary"
                  disabled={updateBriefMutation.isPending}
                  onClick={() => void handleSaveBrief(false)}
                >
                  Salva brief
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary"
                  disabled={updateBriefMutation.isPending}
                  onClick={() => void handleSaveBrief(true)}
                >
                  Approva brief
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--ghost"
                  disabled={generateBriefMutation.isPending}
                  onClick={() => void handleGenerateBrief()}
                >
                  {generateBriefMutation.isPending ? "Rigenerazione…" : "Rigenera brief"}
                </button>
              </>
            )}
          </div>
        </section>

        <div className="seo-drawer__actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={updateMutation.isPending || !title.trim()}
            onClick={() => void handleSaveMetadata()}
          >
            Salva item
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
