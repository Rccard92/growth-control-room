import { useState } from "react";
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

export function GrowthAuditPageDrawer({
  open,
  page,
  findings,
  tasks,
  onClose,
}: GrowthAuditPageDrawerProps) {
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

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

  return (
    <div
      className="growth-audit-page-drawer-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <aside
        className="growth-audit-page-drawer gcr-card"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-label="Dettaglio pagina"
      >
        <header className="growth-audit-page-drawer__header">
          <div className="growth-audit-page-drawer__header-main">
            <p className="gcr-card__label">Dettaglio pagina</p>
            <h3>{getGrowthAuditPageTypeLabel(page.pageType)}</h3>
            <p className="growth-audit-page-drawer__url">
              <code>{page.url}</code>
            </p>
            <div className="growth-audit-page-drawer__meta">
              <span className={getGrowthAuditScoreBadgeClass(page.score)}>
                <span className="growth-audit-page-drawer__score">
                  {formatGrowthAuditScore(page.score)} {getGrowthAuditPageScoreLabel(page.score)}
                </span>
              </span>
              <span>{getGrowthAuditPageInventoryStatusLabel(page.status)}</span>
              <span className={getGrowthAuditSourceBadgeClass(page.source)}>
                {getGrowthAuditPageSourceLabel(page.source)}
              </span>
              <span>HTTP {page.httpStatus ?? "—"}</span>
            </div>
          </div>
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
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

        <GrowthAuditPageTechnicalSummary page={page} />
        <GrowthAuditPageFindingsPanel findings={findings} />
        <GrowthAuditPageTasksPanel tasks={tasks} />
      </aside>
    </div>
  );
}
