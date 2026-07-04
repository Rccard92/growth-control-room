import { useState } from "react";
import { Link } from "react-router-dom";
import type { GrowthAuditPage, GrowthAuditPageResult } from "@gcr/shared";
import { APP_ROUTES } from "../../../routes/config";
import {
  formatGrowthAuditScore,
  getGrowthAuditPageAiMetadata,
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

export interface GrowthAuditPageWorkspaceHeaderProps {
  projectId: string;
  page: GrowthAuditPage;
  runStatus?: string;
  findingsCount: number;
  tasksCount: number;
  latestAiResult?: GrowthAuditPageResult | null;
  isRescanning?: boolean;
  canRescan?: boolean;
  onRescan?: (clearPreviousOpenItems: boolean) => Promise<void>;
  onScrollToSection: (sectionId: string) => void;
}

function truncateUrl(url: string, maxLength = 72): string {
  if (url.length <= maxLength) return url;
  return `${url.slice(0, maxLength - 3)}...`;
}

function formatScoreValue(value?: number | null): string {
  if (value == null) return "—";
  return String(value);
}

export function GrowthAuditPageWorkspaceHeader({
  projectId,
  page,
  runStatus,
  findingsCount,
  tasksCount,
  latestAiResult,
  isRescanning = false,
  canRescan = false,
  onRescan,
  onScrollToSection,
}: GrowthAuditPageWorkspaceHeaderProps) {
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [showRescanConfirm, setShowRescanConfirm] = useState(false);
  const [clearPreviousOpenItems, setClearPreviousOpenItems] = useState(true);
  const [rescanFeedback, setRescanFeedback] = useState<"success" | "error" | null>(null);
  const [rescanMessage, setRescanMessage] = useState<string | null>(null);

  const mappedEntity = mapGrowthAuditPageToSeoEntity(page);
  const shopifyEditable = Boolean(mappedEntity);
  const aiAvailable = page.status === "analyzed";
  const rescanLabel = page.status === "failed" ? "Riprova scansione" : "Riscansiona pagina";
  const aiMeta = getGrowthAuditPageAiMetadata(page);
  const rawOutput = latestAiResult?.rawOutput as Record<string, unknown> | undefined;

  const aiScore = latestAiResult?.score ?? aiMeta?.latestScore ?? null;
  const geoScore =
    (rawOutput?.geoScore as number | undefined) ?? page.geoScore ?? aiMeta?.geoScore ?? null;
  const croScore =
    (rawOutput?.croScore as number | undefined) ?? page.croScore ?? aiMeta?.croScore ?? null;
  const adsScore =
    (rawOutput?.adsReadinessScore as number | undefined) ?? aiMeta?.adsReadinessScore ?? null;

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
    <header className="growth-audit-workspace-header growth-audit-workspace-header--sticky gcr-card">
      <div className="growth-audit-workspace-header__top">
        <Link
          to={APP_ROUTES.projectGrowthAudit(projectId)}
          className="growth-audit-workspace-header__back"
        >
          ← Torna al Growth Audit
        </Link>
      </div>

      <div className="growth-audit-workspace-header__main">
        <div className="growth-audit-workspace-header__identity">
          <p className="growth-audit-workspace-header__type">
            {getGrowthAuditPageTypeLabel(page.pageType)}
          </p>
          <p className="growth-audit-workspace-header__url" title={page.url}>
            {truncateUrl(page.url)}
          </p>
          <div className="growth-audit-workspace-header__badges">
            <span className="growth-audit-workspace-header__badge">
              {getGrowthAuditPageInventoryStatusLabel(page.status)}
            </span>
            <span className={getGrowthAuditSourceBadgeClass(page.source)}>
              {getGrowthAuditPageSourceLabel(page.source)}
            </span>
            <span className="growth-audit-workspace-header__badge">
              HTTP {page.httpStatus ?? "—"}
            </span>
            <span className={getGrowthAuditShopifyLinkBadgeClass(page)}>
              {getGrowthAuditShopifyLinkBadgeLabel(page)}
            </span>
          </div>
        </div>

        <div className="growth-audit-workspace-header__scores">
          <div className="growth-audit-workspace-header__score-hero">
            <span className={getGrowthAuditScoreBadgeClass(page.score)}>
              <span className="growth-audit-workspace-header__score-value">
                {formatGrowthAuditScore(page.score)}
              </span>
            </span>
            <span className="growth-audit-workspace-header__score-label">
              {getGrowthAuditPageScoreLabel(page.score)}
            </span>
            <span className="growth-audit-workspace-header__score-caption">Score tecnico</span>
          </div>
          <div className="growth-audit-workspace-header__score-mini">
            <span>AI {formatGrowthAuditScore(aiScore)}</span>
            <span>GEO {formatScoreValue(geoScore)}</span>
            <span>CRO {formatScoreValue(croScore)}</span>
            <span>Ads {formatScoreValue(adsScore)}</span>
            <span>{findingsCount} problemi</span>
            <span>{tasksCount} task</span>
          </div>
        </div>
      </div>

      <div className="growth-audit-workspace-header__actions">
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
        {shopifyEditable && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("shopify-edit")}
          >
            Modifica Shopify
          </button>
        )}
        {aiAvailable && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("ai-geo-cro")}
          >
            Analizza AI/GEO/CRO
          </button>
        )}
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary gcr-btn--sm"
          disabled={!canRescan || isRescanning || isGrowthAuditRunActive(runStatus)}
          onClick={() => setShowRescanConfirm(true)}
        >
          {isRescanning ? "Riscansione in corso…" : rescanLabel}
        </button>
      </div>

      {showRescanConfirm && (
        <div className="growth-audit-workspace-header__rescan-confirm">
          <p>
            Vuoi riscansionare questa pagina? I problemi e task aperti precedenti verranno
            archiviati come superati e sostituiti dai nuovi risultati.
          </p>
          <label className="growth-audit-workspace-header__rescan-checkbox">
            <input
              type="checkbox"
              checked={clearPreviousOpenItems}
              onChange={(event) => setClearPreviousOpenItems(event.target.checked)}
            />
            Archivia problemi e task aperti precedenti
          </label>
          <div className="growth-audit-workspace-header__rescan-actions">
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
        <div className="growth-audit-workspace-header__rescan-success" role="status">
          {rescanMessage}
        </div>
      )}
      {rescanFeedback === "error" && rescanMessage && (
        <div className="growth-audit-workspace-header__rescan-error" role="alert">
          {rescanMessage}
        </div>
      )}
    </header>
  );
}
