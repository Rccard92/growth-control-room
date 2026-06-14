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
import { AppModal } from "../../ui/AppModal";
import { AppSelect } from "../../ui/AppSelect";
import { AppDatePicker } from "../../ui/AppDatePicker";
import { AppCheckbox } from "../../ui/AppCheckbox";
import {
  useDeleteEditorialItem,
  useGenerateEditorialBrief,
  useRescheduleEditorialItem,
  useUpdateEditorialBrief,
  useUpdateEditorialItem,
} from "../../../hooks/useContentSeoEditorial";

interface EditorialItemModalProps {
  open: boolean;
  item: ContentSeoEditorialItem | null;
  projectId: string;
  allItems: ContentSeoEditorialItem[];
  onClose: () => void;
  onItemUpdated?: (item: ContentSeoEditorialItem) => void;
}

function formatPlannedDate(value: string): string {
  const parsed = new Date(value.slice(0, 10) + "T12:00:00");
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 10);
  return parsed.toLocaleDateString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function EditorialItemModal({
  open,
  item,
  projectId,
  allItems,
  onClose,
  onItemUpdated,
}: EditorialItemModalProps) {
  const updateMutation = useUpdateEditorialItem(projectId);
  const rescheduleMutation = useRescheduleEditorialItem(projectId);
  const deleteMutation = useDeleteEditorialItem(projectId);
  const generateBriefMutation = useGenerateEditorialBrief(projectId);
  const updateBriefMutation = useUpdateEditorialBrief(projectId);

  const [title, setTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [originalPlannedDate, setOriginalPlannedDate] = useState("");
  const [cascadeReschedule, setCascadeReschedule] = useState(false);
  const [status, setStatus] = useState<ContentSeoEditorialStatus>("idea");
  const [objective, setObjective] = useState<ContentSeoEditorialObjective | "">("");
  const [primaryKeyword, setPrimaryKeyword] = useState("");
  const [secondaryKeywords, setSecondaryKeywords] = useState("");
  const [notes, setNotes] = useState("");
  const [brief, setBrief] = useState<EditorialBriefPayload | null>(null);
  const [savedBriefSnapshot, setSavedBriefSnapshot] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!item) return;
    const date = item.plannedDate.slice(0, 10);
    setTitle(item.title);
    setPlannedDate(date);
    setOriginalPlannedDate(date);
    setCascadeReschedule(false);
    setStatus(item.status);
    setObjective(item.objective ?? "");
    setPrimaryKeyword(item.primaryKeyword ?? "");
    setSecondaryKeywords((item.secondaryKeywords ?? []).join(", "));
    setNotes(item.notes ?? "");
    const parsed = parseEditorialBriefPayload(item.briefPayload ?? null);
    setBrief(hasEditorialBrief(item.briefPayload ?? null) ? parsed : null);
    setSavedBriefSnapshot(JSON.stringify(parsed));
    setError(null);
    setWarning(null);
    setSuccess(null);
  }, [item]);

  const briefDirty = useMemo(() => {
    if (!brief) return false;
    return JSON.stringify(brief) !== savedBriefSnapshot;
  }, [brief, savedBriefSnapshot]);

  const dateChanged = plannedDate !== originalPlannedDate;
  const hasFollowingItems = useMemo(() => {
    if (!item) return false;
    return allItems.some(
      (i) =>
        i.id !== item.id && i.plannedDate.slice(0, 10) > originalPlannedDate,
    );
  }, [allItems, item, originalPlannedDate]);

  const showCascadeOption = dateChanged && hasFollowingItems;

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

  async function handleSave() {
    if (!item) return;
    setError(null);
    setWarning(null);
    setSuccess(null);
    try {
      const metadata = {
        title: title.trim(),
        status,
        objective: objective || null,
        primaryKeyword: primaryKeyword.trim() || null,
        secondaryKeywords: secondaryKeywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
        notes: notes.trim() || null,
      };

      if (dateChanged) {
        const updated = await updateMutation.mutateAsync({
          itemId: item.id,
          data: metadata,
        });
        syncItem(updated);

        const rescheduleResult = await rescheduleMutation.mutateAsync({
          itemId: item.id,
          data: {
            plannedDate,
            cascade: cascadeReschedule,
          },
        });
        const current = rescheduleResult.items.find((i) => i.id === item.id);
        if (current) {
          syncItem(current);
          setOriginalPlannedDate(plannedDate);
        }
        if (rescheduleResult.warning) {
          setWarning(rescheduleResult.warning);
        }
        setSuccess(
          cascadeReschedule
            ? "Item e contenuti successivi riprogrammati."
            : "Data aggiornata.",
        );
      } else {
        const updated = await updateMutation.mutateAsync({
          itemId: item.id,
          data: {
            ...metadata,
            plannedDate,
          },
        });
        syncItem(updated);
        setSuccess("Item salvato.");
      }
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

  async function handleGenerateBrief() {
    if (!item) return;
    if (
      brief &&
      briefDirty &&
      !window.confirm("Rigenerando perderai le modifiche non salvate. Continuare?")
    ) {
      return;
    }
    setError(null);
    try {
      const updated = await generateBriefMutation.mutateAsync(item.id);
      syncItem(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante la generazione del brief.");
    }
  }

  async function handleSaveBrief(approve = false) {
    if (!item || !brief) return;
    setError(null);
    try {
      const updated = await updateBriefMutation.mutateAsync({
        itemId: item.id,
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

  if (!item) return null;

  const hasBrief = Boolean(brief);
  const subtitle = [
    CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType],
    formatPlannedDate(item.plannedDate),
    CONTENT_SEO_EDITORIAL_STATUS_LABELS[item.status],
  ].join(" · ");

  const isSaving = updateMutation.isPending || rescheduleMutation.isPending;

  const footer = (
    <>
      <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
        Chiudi
      </button>
      <button
        type="button"
        className="gcr-btn gcr-btn--danger"
        disabled={deleteMutation.isPending}
        onClick={() => void handleDelete()}
      >
        Elimina
      </button>
      <button
        type="button"
        className="gcr-btn gcr-btn--primary"
        disabled={isSaving || !title.trim()}
        onClick={() => void handleSave()}
      >
        {isSaving ? "Salvataggio…" : "Salva item"}
      </button>
    </>
  );

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Dettaglio contenuto editoriale"
      subtitle={subtitle}
      maxWidth="lg"
      footer={footer}
    >
      <div className="editorial-item-modal">
        {error && <div className="gcr-alert gcr-alert--error">{error}</div>}
        {warning && <div className="gcr-alert gcr-alert--warning">{warning}</div>}
        {success && <div className="gcr-alert gcr-alert--success">{success}</div>}

        <section className="editorial-item-modal__section">
          <label className="gcr-field">
            <span className="gcr-field__label">Titolo</span>
            <input
              className="gcr-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>

          <AppDatePicker
            label="Data pianificata"
            value={plannedDate}
            onChange={setPlannedDate}
          />

          {showCascadeOption && (
            <AppCheckbox
              variant="card"
              checked={cascadeReschedule}
              onChange={setCascadeReschedule}
              label="Riprogramma anche i contenuti successivi mantenendo la frequenza del piano"
              description="Se attivo, tutti i contenuti successivi verranno spostati dello stesso numero di giorni."
            />
          )}

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

          {item.linkedShopifyProductTitle && (
            <p className="editorial-item-modal__linked">
              Prodotto collegato: <strong>{item.linkedShopifyProductTitle}</strong>
            </p>
          )}
        </section>

        <section className="editorial-item-modal__section editorial-item-modal__brief">
          <h4>Brief SEO</h4>
          {hasBrief ? (
            <EditorialBriefEditor value={brief!} onChange={setBrief} />
          ) : (
            <p className="gcr-card__description">Brief SEO non ancora generato</p>
          )}

          <div className="editorial-item-modal__brief-actions">
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
      </div>
    </AppModal>
  );
}
