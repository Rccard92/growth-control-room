import { useState } from "react";
import { Link } from "react-router-dom";
import type { GrowthAuditPage } from "@gcr/shared";
import { APP_ROUTES } from "../../../routes/config";
import {
  formatGrowthAuditScore,
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditShopifyLinkBadgeClass,
  getGrowthAuditShopifyLinkBadgeLabel,
  getGrowthAuditSourceBadgeClass,
  isGrowthAuditRunActive,
  mapGrowthAuditPageToSeoEntity,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageDetailHeaderProps {
  projectId: string;
  page: GrowthAuditPage;
  runStatus?: string;
  isRescanning?: boolean;
  canRescan?: boolean;
  onRescan?: (clearPreviousOpenItems: boolean) => Promise<void>;
  onScrollToSection: (sectionId: string) => void;
}

export function GrowthAuditPageDetailHeader({
  projectId,
  page,
  runStatus,
  isRescanning = false,
  canRescan = false,
  onRescan,
  onScrollToSection,
}: GrowthAuditPageDetailHeaderProps) {
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [showRescanConfirm, setShowRescanConfirm] = useState(false);
  const [clearPreviousOpenItems, setClearPreviousOpenItems] = useState(true);
  const [rescanFeedback, setRescanFeedback] = useState<"success" | "error" | null>(null);
  const [rescanMessage, setRescanMessage] = useState<string | null>(null);

  const mappedEntity = mapGrowthAuditPageToSeoEntity(page);
  const shopifyEditable = Boolean(mappedEntity);
  const aiAvailable = page.status === "analyzed";
  const rescanLabel = page.status === "failed" ? "Riprova scansione" : "Riscansiona pagina";

  async function handleCopyUrl() {
    try {
      await navigator.clipboard.writeText(page.url);
      setCopyFeedback("Copiato");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    } catch {
      setCopyFeedback("Errore copia");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    }
  }

  async function handleConfirmRescan() {
    if (!onRescan) return;
    setRescanFeedback(null);
    setRescanMessage(null);
    try {
      await onRescan(clearPreviousOpenItems);
      setShowRescanConfirm(false);
      setRescanFeedback("success");
      setRescanMessage("Pagina riscansionata. Score aggiornato.");
    } catch (error) {
      setRescanFeedback("error");
      setRescanMessage(
        error instanceof Error ? error.message : "Riscansione non riuscita. Riprova.",
      );
    }
  }

  return (
    <>
      <div className="growth-audit-page-detail__topbar">
        <div className="growth-audit-page-detail__topbar-left">
          <Link
            to={APP_ROUTES.projectGrowthAudit(projectId)}
            className="growth-audit-page-detail__back-link"
          >
            ← Torna all&apos;audit
          </Link>
          <p className="growth-audit-page-detail__breadcrumb">
            Growth Audit → Dettaglio pagina
          </p>
        </div>
        <a
          href={page.url}
          target="_blank"
          rel="noopener noreferrer"
          className="gcr-btn gcr-btn--secondary gcr-btn--sm"
        >
          Apri pagina
        </a>
      </div>

      <header className="growth-audit-page-detail__hero gcr-card">
        <div className="growth-audit-page-detail__hero-main">
          <p className="growth-audit-page-detail__hero-label">Dettaglio pagina</p>
          <h1 className="growth-audit-page-detail__hero-title">
            {getGrowthAuditPageTypeLabel(page.pageType)}
          </h1>
          <p className="growth-audit-page-detail__hero-url" title={page.url}>
            {page.url}
          </p>
          <div className="growth-audit-page-detail__hero-score">
            <span className={getGrowthAuditScoreBadgeClass(page.score)}>
              <span className="growth-audit-page-detail__hero-score-value">
                {formatGrowthAuditScore(page.score)}
              </span>
            </span>
            <span className="growth-audit-page-detail__hero-score-label">
              {getGrowthAuditPageScoreLabel(page.score)}
            </span>
          </div>
          <div className="growth-audit-page-detail__hero-badges">
            <span className="growth-audit-page-detail__badge">
              {getGrowthAuditPageInventoryStatusLabel(page.status)}
            </span>
            <span className={getGrowthAuditSourceBadgeClass(page.source)}>
              {getGrowthAuditPageSourceLabel(page.source)}
            </span>
            <span className="growth-audit-page-detail__badge">HTTP {page.httpStatus ?? "—"}</span>
            <span className={getGrowthAuditShopifyLinkBadgeClass(page)}>
              {getGrowthAuditShopifyLinkBadgeLabel(page)}
            </span>
          </div>
        </div>

        <div className="growth-audit-page-detail__hero-actions">
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
            disabled={!canRescan || isRescanning || isGrowthAuditRunActive(runStatus)}
            onClick={() => setShowRescanConfirm(true)}
          >
            {isRescanning ? "Riscansione in corso…" : rescanLabel}
          </button>
          {aiAvailable && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("section-ai")}
            >
              Analizza AI/GEO/CRO
            </button>
          )}
          {shopifyEditable && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("shopify-edit")}
            >
              Modifica Shopify
            </button>
          )}
        </div>

        {showRescanConfirm && (
          <div className="growth-audit-page-detail__rescan-confirm">
            <p>
              Vuoi riscansionare questa pagina? I problemi/task aperti precedenti verranno
              archiviati come superati e sostituiti dai nuovi risultati.
            </p>
            <label className="growth-audit-page-detail__rescan-checkbox">
              <input
                type="checkbox"
                checked={clearPreviousOpenItems}
                onChange={(event) => setClearPreviousOpenItems(event.target.checked)}
              />
              Archivia problemi e task aperti precedenti
            </label>
            <div className="growth-audit-page-detail__rescan-actions">
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
          <div className="growth-audit-page-detail__rescan-success" role="status">
            {rescanMessage}
          </div>
        )}
        {rescanFeedback === "error" && rescanMessage && (
          <div className="growth-audit-page-detail__rescan-error" role="alert">
            {rescanMessage}
          </div>
        )}
      </header>
    </>
  );
}
