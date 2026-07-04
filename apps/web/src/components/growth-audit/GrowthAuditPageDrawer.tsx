import { useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditTask } from "@gcr/shared";
import {
  formatGrowthAuditScore,
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditSourceBadgeClass,
  isGrowthAuditRunActive,
} from "../../lib/growth-audit-utils";
import { GrowthAuditPageFindingsPanel } from "./GrowthAuditPageFindingsPanel";
import { GrowthAuditPageTasksPanel } from "./GrowthAuditPageTasksPanel";
import { GrowthAuditPageTechnicalSummary } from "./GrowthAuditPageTechnicalSummary";

interface GrowthAuditPageDrawerProps {
  open: boolean;
  page: GrowthAuditPage | null;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  projectId?: string;
  runId?: string;
  runStatus?: string;
  isRescanning?: boolean;
  onRescan?: (input: {
    runId: string;
    pageId: string;
    clearPreviousOpenItems: boolean;
  }) => Promise<void>;
  onClose: () => void;
}

export function handleDrawerEscapeKey(event: KeyboardEvent, onClose: () => void): void {
  if (event.key === "Escape") onClose();
}

export function GrowthAuditPageDrawer({
  open,
  page,
  findings,
  tasks,
  projectId,
  runId,
  runStatus,
  isRescanning = false,
  onRescan,
  onClose,
}: GrowthAuditPageDrawerProps) {
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [showRescanConfirm, setShowRescanConfirm] = useState(false);
  const [clearPreviousOpenItems, setClearPreviousOpenItems] = useState(true);
  const [rescanFeedback, setRescanFeedback] = useState<"success" | "error" | null>(null);
  const [rescanMessage, setRescanMessage] = useState<string | null>(null);
  const [showUpdatedBadge, setShowUpdatedBadge] = useState(false);
  const titleId = useId();

  useEffect(() => {
    if (!open || typeof document === "undefined") return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      handleDrawerEscapeKey(event, onClose);
    };
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open) {
      setShowRescanConfirm(false);
      setRescanFeedback(null);
      setRescanMessage(null);
      setShowUpdatedBadge(false);
    }
  }, [open, page?.id]);

  if (!open || !page) return null;

  async function handleCopyUrl() {
    try {
      await navigator.clipboard.writeText(page!.url);
      setCopyFeedback("Copiato");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    } catch {
      setCopyFeedback("Errore copia");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    }
  }

  const scoreLabel = getGrowthAuditPageScoreLabel(page.score);
  const canRescan = Boolean(
    projectId &&
      runId &&
      page.id &&
      page.status !== "analyzing" &&
      !isGrowthAuditRunActive(runStatus) &&
      onRescan,
  );
  const rescanLabel = page.status === "failed" ? "Riprova scansione" : "Riscansiona pagina";

  async function handleConfirmRescan() {
    if (!onRescan || !runId || !page) return;

    setRescanFeedback(null);
    setRescanMessage(null);
    try {
      await onRescan({
        runId,
        pageId: page.id,
        clearPreviousOpenItems,
      });
      setShowRescanConfirm(false);
      setRescanFeedback("success");
      setRescanMessage("Pagina riscansionata. Score aggiornato.");
      setShowUpdatedBadge(true);
      window.setTimeout(() => setShowUpdatedBadge(false), 5000);
    } catch (error) {
      setRescanFeedback("error");
      setRescanMessage(
        error instanceof Error ? error.message : "Riscansione non riuscita. Riprova.",
      );
    }
  }

  const drawerContent = (
    <div
      className="growth-audit-page-drawer-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <aside
        className="growth-audit-page-drawer"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <header className="growth-audit-page-drawer__header">
          <div className="growth-audit-page-drawer__header-main">
            <p className="growth-audit-page-drawer__label">Dettaglio pagina</p>
            <h3 id={titleId}>{getGrowthAuditPageTypeLabel(page.pageType)}</h3>
            <p className="growth-audit-page-drawer__url" title={page.url}>
              {page.url}
            </p>
            <div className="growth-audit-page-drawer__score-hero">
              <span className={getGrowthAuditScoreBadgeClass(page.score)}>
                <span className="growth-audit-page-drawer__score-value">
                  {formatGrowthAuditScore(page.score)}
                </span>
              </span>
              <span className="growth-audit-page-drawer__score-label">{scoreLabel}</span>
              {showUpdatedBadge && (
                <span className="growth-audit-page-drawer__updated-badge">Aggiornata ora</span>
              )}
            </div>
            <div className="growth-audit-page-drawer__badges">
              <span className="growth-audit-page-drawer__badge">
                {getGrowthAuditPageInventoryStatusLabel(page.status)}
              </span>
              <span className={getGrowthAuditSourceBadgeClass(page.source)}>
                {getGrowthAuditPageSourceLabel(page.source)}
              </span>
              <span className="growth-audit-page-drawer__badge">
                HTTP {page.httpStatus ?? "—"}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onClose}
            aria-label="Chiudi"
          >
            Chiudi
          </button>
        </header>

        <div className="growth-audit-page-drawer__actions">
          <a
            href={page.url}
            target="_blank"
            rel="noopener noreferrer"
            className="gcr-btn gcr-btn--primary gcr-btn--sm"
          >
            Apri pagina
          </a>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => void handleCopyUrl()}
          >
            {copyFeedback ?? "Copia URL"}
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            disabled={!canRescan || isRescanning}
            onClick={() => setShowRescanConfirm(true)}
          >
            {isRescanning ? "Riscansione in corso…" : rescanLabel}
          </button>
        </div>

        <p className="growth-audit-page-drawer__rescan-note">
          Usalo dopo aver corretto title, meta, immagini, schema o altri elementi tecnici.
        </p>

        {showRescanConfirm && (
          <div className="growth-audit-page-drawer__rescan-confirm">
            <p>
              Vuoi riscansionare questa pagina? I problemi/task aperti precedenti verranno
              archiviati come superati e sostituiti dai nuovi risultati.
            </p>
            <label className="growth-audit-page-drawer__rescan-checkbox">
              <input
                type="checkbox"
                checked={clearPreviousOpenItems}
                onChange={(event) => setClearPreviousOpenItems(event.target.checked)}
              />
              Archivia problemi e task aperti precedenti
            </label>
            <div className="growth-audit-page-drawer__rescan-actions">
              <button
                type="button"
                className="gcr-btn gcr-btn--primary gcr-btn--sm"
                disabled={isRescanning}
                onClick={() => void handleConfirmRescan()}
              >
                {isRescanning ? "Riscansione in corso…" : "Conferma rescan"}
              </button>
              <button
                type="button"
                className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                disabled={isRescanning}
                onClick={() => setShowRescanConfirm(false)}
              >
                Annulla
              </button>
            </div>
          </div>
        )}

        {rescanFeedback === "success" && rescanMessage && (
          <div className="growth-audit-page-drawer__rescan-success" role="status">
            {rescanMessage}
          </div>
        )}

        {rescanFeedback === "error" && rescanMessage && (
          <div className="growth-audit-page-drawer__rescan-error" role="alert">
            {rescanMessage}
          </div>
        )}

        {page.status === "failed" && page.errorMessage && (
          <div className="growth-audit-page-drawer__error" role="alert">
            {page.errorMessage}
          </div>
        )}

        <GrowthAuditPageFindingsPanel findings={findings} />
        <GrowthAuditPageTasksPanel tasks={tasks} />
        <GrowthAuditPageTechnicalSummary page={page} />
      </aside>
    </div>
  );

  if (typeof document === "undefined") {
    return drawerContent;
  }

  return createPortal(drawerContent, document.body);
}
