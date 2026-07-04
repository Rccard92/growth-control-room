import { useEffect, useId, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditTask } from "@gcr/shared";
import { SeoEntityEditPanel } from "../content/optimizer/SeoEntityEditPanel";
import { useCollectionSeoDetail, useProductSeoDetail, useProductsSeo, useCollectionsSeo } from "../../hooks/useContentSeo";
import {
  formatGrowthAuditScore,
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditSourceEntityTypeLabel,
  isGrowthAuditPageShopifyLinked,
  isGrowthAuditRunActive,
  mapGrowthAuditPageToSeoEntity,
} from "../../lib/growth-audit-utils";
import { GrowthAuditPageAiAnalysisPanel } from "./GrowthAuditPageAiAnalysisPanel";
import { GrowthAuditPageFindingsPanel } from "./GrowthAuditPageFindingsPanel";
import { GrowthAuditPageImprovementPanel } from "./GrowthAuditPageImprovementPanel";
import { GrowthAuditPageTasksPanel } from "./GrowthAuditPageTasksPanel";
import { GrowthAuditPageTechnicalSummary } from "./GrowthAuditPageTechnicalSummary";

type DrawerTabId = "overview" | "improvements" | "problems" | "tasks" | "technical" | "ai" | "shopify";

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

function supportsShopifyEditTab(page: GrowthAuditPage): boolean {
  return Boolean(mapGrowthAuditPageToSeoEntity(page));
}

function isShopifyEditComingSoon(page: GrowthAuditPage): boolean {
  return (
    page.sourceEntityType === "shopify_page" || page.sourceEntityType === "shopify_article"
  );
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
  const [activeTab, setActiveTab] = useState<DrawerTabId>("overview");
  const titleId = useId();

  const mappedSeoEntity = page ? mapGrowthAuditPageToSeoEntity(page) : null;
  const shopifyEditTabVisible = page ? supportsShopifyEditTab(page) : false;

  const productDetailQuery = useProductSeoDetail(
    projectId ?? "",
    activeTab === "shopify" && mappedSeoEntity?.entityType === "product"
      ? mappedSeoEntity.entityId
      : null,
  );
  const collectionDetailQuery = useCollectionSeoDetail(
    projectId ?? "",
    activeTab === "shopify" && mappedSeoEntity?.entityType === "collection"
      ? mappedSeoEntity.entityId
      : null,
  );

  const shopifyFlagsEnabled = Boolean(
    projectId && activeTab === "shopify" && shopifyEditTabVisible,
  );
  const productsSeoQuery = useProductsSeo(
    projectId,
    shopifyFlagsEnabled && mappedSeoEntity?.entityType === "product",
  );
  const collectionsSeoQuery = useCollectionsSeo(
    projectId,
    shopifyFlagsEnabled && mappedSeoEntity?.entityType === "collection",
  );

  const seoDetailLoading =
    mappedSeoEntity?.entityType === "product"
      ? productDetailQuery.isLoading
      : collectionDetailQuery.isLoading;

  const seoDetailError =
    mappedSeoEntity?.entityType === "product"
      ? productDetailQuery.isError
      : collectionDetailQuery.isError;

  const openaiConfigured =
    productsSeoQuery.data?.openaiConfigured ??
    collectionsSeoQuery.data?.openaiConfigured ??
    false;
  const writeProductsAvailable =
    productsSeoQuery.data?.writeProductsAvailable ??
    collectionsSeoQuery.data?.writeProductsAvailable ??
    false;

  const tabs = useMemo(() => {
    const base: { id: DrawerTabId; label: string }[] = [
      { id: "overview", label: "Overview" },
      { id: "improvements", label: "Miglioramenti" },
      { id: "problems", label: "Problemi" },
      { id: "tasks", label: "Task" },
      { id: "technical", label: "Dati tecnici" },
    ];
    if (page?.status === "analyzed") {
      base.push({ id: "ai", label: "AI/GEO/CRO" });
    }
    if (shopifyEditTabVisible) {
      base.push({ id: "shopify", label: "Modifica Shopify" });
    }
    return base;
  }, [shopifyEditTabVisible, page?.status]);

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
      setActiveTab("overview");
    }
  }, [open, page?.id]);

  if (!open || !page) return null;

  const currentPage = page;

  async function handleCopyUrl() {
    try {
      await navigator.clipboard.writeText(currentPage.url);
      setCopyFeedback("Copiato");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    } catch {
      setCopyFeedback("Errore copia");
      window.setTimeout(() => setCopyFeedback(null), 2000);
    }
  }

  const scoreLabel = getGrowthAuditPageScoreLabel(currentPage.score);
  const canRescan = Boolean(
    projectId &&
      runId &&
      currentPage.id &&
      currentPage.status !== "analyzing" &&
      !isGrowthAuditRunActive(runStatus) &&
      onRescan,
  );
  const rescanLabel = currentPage.status === "failed" ? "Riprova scansione" : "Riscansiona pagina";
  const shopifyLinked = isGrowthAuditPageShopifyLinked(currentPage);

  async function handleConfirmRescan() {
    if (!onRescan || !runId) return;

    setRescanFeedback(null);
    setRescanMessage(null);
    try {
      await onRescan({
        runId,
        pageId: currentPage.id,
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

  function renderShopifyOverviewCard() {
    return (
      <section className="growth-audit-page-drawer__section growth-audit-shopify-entity-card">
        <h4 className="growth-audit-page-drawer__section-title">
          {shopifyLinked ? "Entità Shopify collegata" : "Entità Shopify"}
        </h4>
        {shopifyLinked ? (
          <div className="growth-audit-shopify-entity-card__body">
            <p>
              <span className="growth-audit-shopify-entity-card__label">Tipo:</span>{" "}
              {getGrowthAuditSourceEntityTypeLabel(currentPage.sourceEntityType)}
            </p>
            {currentPage.sourceEntityTitle && (
              <p>
                <span className="growth-audit-shopify-entity-card__label">Titolo:</span>{" "}
                {currentPage.sourceEntityTitle}
              </p>
            )}
            {currentPage.sourceEntityHandle && (
              <p>
                <span className="growth-audit-shopify-entity-card__label">Handle:</span>{" "}
                {currentPage.sourceEntityHandle}
              </p>
            )}
            {shopifyEditTabVisible && (
              <p className="growth-audit-shopify-entity-card__microcopy">
                Usa la tab Modifica Shopify per aggiornare title, meta e alt immagini, poi
                riscansiona la pagina.
              </p>
            )}
            {isShopifyEditComingSoon(currentPage) && (
              <p className="growth-audit-shopify-entity-card__microcopy">
                Modifica Shopify per pagine e articoli in arrivo.
              </p>
            )}
          </div>
        ) : (
          <span className="growth-audit-shopify-entity-badge growth-audit-shopify-entity-badge--unlinked">
            Nessuna entità Shopify collegata
          </span>
        )}
      </section>
    );
  }

  function renderShopifyEditTab() {
    if (!projectId) {
      return (
        <p className="growth-audit-page-drawer__tab-placeholder">
          Progetto non disponibile per la modifica Shopify.
        </p>
      );
    }

    if (shopifyEditTabVisible && mappedSeoEntity) {
      return (
        <div className="growth-audit-page-drawer__shopify-edit">
          <SeoEntityEditPanel
            embedded
            projectId={projectId}
            entityType={mappedSeoEntity.entityType}
            entityId={mappedSeoEntity.entityId}
            title={currentPage.sourceEntityTitle ?? currentPage.title ?? currentPage.url}
            productDetail={
              mappedSeoEntity.entityType === "product" ? productDetailQuery.data : undefined
            }
            collectionDetail={
              mappedSeoEntity.entityType === "collection"
                ? collectionDetailQuery.data
                : undefined
            }
            detailLoading={seoDetailLoading}
            detailError={seoDetailError}
            detailErrorMessage={
              seoDetailError ? "Impossibile caricare i dati SEO dell'entità." : undefined
            }
            openaiConfigured={openaiConfigured}
            writeProductsAvailable={writeProductsAvailable}
            onDetailRefresh={() => {
              if (mappedSeoEntity.entityType === "product") {
                void productDetailQuery.refetch();
              } else {
                void collectionDetailQuery.refetch();
              }
            }}
          />
        </div>
      );
    }

    if (isShopifyEditComingSoon(currentPage)) {
      return (
        <p className="growth-audit-page-drawer__tab-placeholder">
          Modifica Shopify per pagine e articoli in arrivo.
        </p>
      );
    }

    return (
      <p className="growth-audit-page-drawer__tab-placeholder">
        Questa pagina non è collegata a un&apos;entità Shopify modificabile.
      </p>
    );
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
            <h3 id={titleId}>{getGrowthAuditPageTypeLabel(currentPage.pageType)}</h3>
            <p className="growth-audit-page-drawer__url" title={currentPage.url}>
              {currentPage.url}
            </p>
            <div className="growth-audit-page-drawer__score-hero">
              <span className={getGrowthAuditScoreBadgeClass(currentPage.score)}>
                <span className="growth-audit-page-drawer__score-value">
                  {formatGrowthAuditScore(currentPage.score)}
                </span>
              </span>
              <span className="growth-audit-page-drawer__score-label">{scoreLabel}</span>
              {showUpdatedBadge && (
                <span className="growth-audit-page-drawer__updated-badge">Aggiornata ora</span>
              )}
            </div>
            <div className="growth-audit-page-drawer__badges">
              <span className="growth-audit-page-drawer__badge">
                {getGrowthAuditPageInventoryStatusLabel(currentPage.status)}
              </span>
              <span className={getGrowthAuditSourceBadgeClass(currentPage.source)}>
                {getGrowthAuditPageSourceLabel(currentPage.source)}
              </span>
              <span className="growth-audit-page-drawer__badge">
                HTTP {currentPage.httpStatus ?? "—"}
              </span>
              {shopifyLinked && (
                <span className="growth-audit-shopify-entity-badge growth-audit-shopify-entity-badge--linked">
                  Shopify collegata
                </span>
              )}
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
            href={currentPage.url}
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

        {currentPage.status === "failed" && currentPage.errorMessage && (
          <div className="growth-audit-page-drawer__error" role="alert">
            {currentPage.errorMessage}
          </div>
        )}

        <div
          className="growth-audit-page-drawer__tabs"
          role="tablist"
          aria-label="Sezioni dettaglio pagina"
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`growth-audit-page-drawer__tab ${
                activeTab === tab.id ? "growth-audit-page-drawer__tab--active" : ""
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="growth-audit-page-drawer__tab-panels">
          {activeTab === "overview" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              {renderShopifyOverviewCard()}
              <section className="growth-audit-page-drawer__section">
                <h4 className="growth-audit-page-drawer__section-title">Riepilogo</h4>
                <p>
                  Score tecnico {formatGrowthAuditScore(currentPage.score)} — {scoreLabel}. Stato:{" "}
                  {getGrowthAuditPageInventoryStatusLabel(currentPage.status)}.
                </p>
              </section>
            </div>
          )}

          {activeTab === "improvements" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              <GrowthAuditPageImprovementPanel page={currentPage} findings={findings} />
            </div>
          )}

          {activeTab === "problems" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              <GrowthAuditPageFindingsPanel findings={findings} />
            </div>
          )}

          {activeTab === "tasks" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              <GrowthAuditPageTasksPanel tasks={tasks} />
            </div>
          )}

          {activeTab === "technical" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              <GrowthAuditPageTechnicalSummary page={currentPage} />
            </div>
          )}

          {activeTab === "ai" && projectId && runId && currentPage.status === "analyzed" && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              <GrowthAuditPageAiAnalysisPanel
                projectId={projectId}
                runId={runId}
                page={currentPage}
                runStatus={runStatus}
              />
            </div>
          )}

          {activeTab === "shopify" && shopifyEditTabVisible && (
            <div className="growth-audit-page-drawer__tab-panel" role="tabpanel">
              {renderShopifyEditTab()}
            </div>
          )}
        </div>
      </aside>
    </div>
  );

  if (typeof document === "undefined") {
    return drawerContent;
  }

  return createPortal(drawerContent, document.body);
}
