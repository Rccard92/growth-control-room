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
} from "../../lib/growth-audit-utils";
import { GrowthAuditPageFindingsPanel } from "./GrowthAuditPageFindingsPanel";
import { GrowthAuditPageTasksPanel } from "./GrowthAuditPageTasksPanel";
import { GrowthAuditPageTechnicalSummary } from "./GrowthAuditPageTechnicalSummary";

interface GrowthAuditPageDrawerProps {
  open: boolean;
  page: GrowthAuditPage | null;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
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
  onClose,
}: GrowthAuditPageDrawerProps) {
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
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
          <button type="button" className="gcr-btn gcr-btn--secondary gcr-btn--sm" disabled>
            Riscansiona pagina — in arrivo
          </button>
        </div>

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
