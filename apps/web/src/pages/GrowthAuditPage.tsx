import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import type {
  GrowthAuditInventoryFilter,
  GrowthAuditPageStatusFilter,
  GrowthAuditScoreFilter,
} from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { GrowthAuditPriorityDashboard } from "../components/growth-audit/GrowthAuditPriorityDashboard";
import {
  useGrowthAuditFindings,
  useGrowthAuditRun,
  useGrowthAuditRuns,
  useGrowthAuditTasks,
  useStartGrowthAuditRun,
} from "../hooks/useGrowthAudit";
import { useProject } from "../hooks/useProjects";
import {
  GROWTH_AUDIT_INVENTORY_FILTERS,
  GROWTH_AUDIT_MAX_PAGES_OPTIONS,
  GROWTH_AUDIT_SCORE_FILTERS,
  GROWTH_AUDIT_STATUS_FILTERS,
  aggregatePageInventory,
  countFindingsByPageId,
  filterInventoryPages,
  filterInventoryPagesByScore,
  filterInventoryPagesByStatus,
  formatGrowthAuditScore,
  formatPageFindingsCount,
  getDefaultRootUrl,
  getGrowthAuditDashboardKpiItems,
  getGrowthAuditInventoryFilterLabel,
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditPublicDomainDisplay,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditSeverityBadgeClass,
  getGrowthAuditShopifyLinkBadgeClass,
  getGrowthAuditShopifyLinkBadgeLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditStatusLabel,
  getInventoryKpiItems,
  getInventoryMessage,
  getTopOpenTasks,
  getTopPriorityFindings,
} from "../lib/growth-audit-utils";
import { APP_ROUTES } from "../routes/config";

const GROWTH_AUDIT_FLOW_STEPS = [
  "Scansiona sito",
  "Classifica pagine",
  "Analizza priorità",
  "Correggi e riscansiona",
] as const;

const GROWTH_AUDIT_ROADMAP = [
  "Performance e Core Web Vitals via PageSpeed/CrUX",
  "Search Console: query, CTR, posizionamento e indicizzazione",
  "GA4/Google Ads: priorità economiche e landing ads",
  "Batch AI controllato sulle top pagine",
  "Crawl avanzato con Firecrawl/DataForSEO",
] as const;

const GROWTH_AUDIT_AI_NEXT_BULLETS = [
  "Prodotto: SEO ecommerce, schema Product, immagini, CRO e trust.",
  "Blog: contenuto, intent, E-E-A-T, GEO e linking interno.",
  "Collection: intent commerciale, schema, testo categoria e UX catalogo.",
] as const;

const DASHBOARD_SUBTITLE =
  "Priorità operative, pagine da correggere e stato delle analisi.";

const ONBOARDING_SUBTITLE =
  "Analizza sito, pagine, contenuti, SEO, GEO, CRO e priorità operative per aumentare performance organiche e ritorno ads.";

function formatGrowthAuditRunDate(value?: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function GrowthAuditPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: runs } = useGrowthAuditRuns(projectId);
  const startRun = useStartGrowthAuditRun(projectId);

  const latestRun = runs?.[0];
  const [rootUrlOverride, setRootUrlOverride] = useState<string | null>(null);
  const [maxPages, setMaxPages] = useState<number>(50);
  const [inventoryFilter, setInventoryFilter] = useState<GrowthAuditInventoryFilter>("all");
  const [scoreFilter, setScoreFilter] = useState<GrowthAuditScoreFilter>("all");
  const [statusFilter, setStatusFilter] = useState<GrowthAuditPageStatusFilter>("all");
  const [activeRunId, setActiveRunId] = useState<string | undefined>();

  useEffect(() => {
    if (activeRunId) return;
    if (latestRun && latestRun.status !== "completed" && latestRun.status !== "failed") {
      setActiveRunId(latestRun.id);
    } else if (latestRun?.status === "completed") {
      setActiveRunId(latestRun.id);
    }
  }, [runs, activeRunId, latestRun]);

  const resolvedRunId = activeRunId ?? latestRun?.id;

  const { data: runDetail } = useGrowthAuditRun(projectId, resolvedRunId, Boolean(resolvedRunId));
  const runStatus = runDetail?.run.status;
  const { data: findings = [] } = useGrowthAuditFindings(
    projectId,
    resolvedRunId,
    undefined,
    runStatus,
    Boolean(resolvedRunId),
  );
  const { data: tasks = [] } = useGrowthAuditTasks(
    projectId,
    resolvedRunId,
    { status: "open" },
    runStatus,
    Boolean(resolvedRunId),
  );

  const activeRun = runDetail?.run;
  const pages = runDetail?.pages ?? [];
  const events = runDetail?.events ?? [];
  const recentEvents = [...events].reverse().slice(0, 5);
  const summary = activeRun?.summary ?? null;
  const summaryMessage = typeof summary?.message === "string" ? summary.message : null;
  const inventoryMessage = getInventoryMessage(activeRun?.pagesDiscovered ?? 0, summary);

  const defaultRootUrl = useMemo(
    () =>
      getDefaultRootUrl({
        rootUrlOverride,
        activeRun,
        latestRun,
      }),
    [rootUrlOverride, activeRun, latestRun],
  );
  const rootUrl = rootUrlOverride ?? defaultRootUrl;

  const hasRuns = Boolean(runs?.length);
  const isOnboardingMode = !hasRuns && !activeRun;
  const isDashboardMode = hasRuns || Boolean(activeRun);
  const isRunInProgress = Boolean(
    activeRun && !["completed", "failed", "partial_failed"].includes(activeRun.status),
  );

  const findingsByPageId = useMemo(() => countFindingsByPageId(findings), [findings]);
  const filteredPages = useMemo(() => {
    const byType = filterInventoryPages(pages, inventoryFilter);
    const byScore = filterInventoryPagesByScore(byType, scoreFilter);
    return filterInventoryPagesByStatus(byScore, statusFilter);
  }, [pages, inventoryFilter, scoreFilter, statusFilter]);
  const inventoryCounts = useMemo(() => aggregatePageInventory(pages), [pages]);
  const inventoryKpiItems = useMemo(
    () => getInventoryKpiItems(pages, summary),
    [pages, summary],
  );
  const dashboardKpiItems = useMemo(
    () =>
      getGrowthAuditDashboardKpiItems(
        activeRun,
        pages,
        runDetail?.findingsCount,
        runDetail?.tasksCount,
      ),
    [activeRun, pages, runDetail?.findingsCount, runDetail?.tasksCount],
  );
  const priorityFindings = useMemo(() => getTopPriorityFindings(findings, 10), [findings]);
  const openTasks = useMemo(() => getTopOpenTasks(tasks, 10), [tasks]);
  const pageUrlById = useMemo(() => {
    const map: Record<string, string> = {};
    for (const page of pages) {
      map[page.id] = page.url;
    }
    return map;
  }, [pages]);

  const showInventoryKpis =
    isDashboardMode &&
    activeRun?.status === "completed" &&
    pages.length > 0 &&
    !activeRun.siteScore &&
    !summary?.averageTechnicalScore;
  const showDashboardKpis =
    isDashboardMode &&
    (Boolean(activeRun?.siteScore != null || summary?.averageTechnicalScore != null) ||
      activeRun?.status === "analyzing" ||
      activeRun?.status === "partial_failed" ||
      pages.length > 0);
  const showTechnicalSections =
    activeRun?.status === "completed" ||
    activeRun?.status === "partial_failed" ||
    activeRun?.status === "analyzing";

  const showPriorityDashboard = Boolean(
    activeRun &&
      pages.length > 0 &&
      resolvedRunId &&
      ["completed", "partial_failed", "failed", "analyzing"].includes(activeRun.status),
  );

  const lastScanLabel =
    formatGrowthAuditRunDate(activeRun?.completedAt) ??
    formatGrowthAuditRunDate(activeRun?.updatedAt) ??
    formatGrowthAuditRunDate(activeRun?.startedAt);

  const handleStartAudit = async () => {
    const trimmed = rootUrl.trim();
    if (!trimmed) return;

    const response = await startRun.mutateAsync({
      rootUrl: trimmed,
      provider: "openai",
      auditMode: "full_site_mvp",
      maxPages,
      includeAiAnalysis: false,
    });
    setActiveRunId(response.run.id);
  };

  const isStartDisabled = !rootUrl.trim() || startRun.isPending;

  const scanFormFields = (
    <>
      <div className="growth-audit-full-site__header">
        <div>
          <h2 className="growth-audit-full-site__title">Scansione sito</h2>
          <p className="growth-audit-full-site__description">
            Scopre URL da sitemap e Shopify, classifica le pagine e avvia controlli tecnici
            deterministici.
          </p>
          <p className="growth-audit-full-site__note">
            Le analisi AI/GEO/CRO avanzate si lanciano sulle pagine prioritarie.
          </p>
        </div>
      </div>

      <div className="growth-audit-skeleton-banner">
        Scansione tecnica attiva: title, meta, canonical, H1, schema, immagini e link. Questa
        scansione è deterministica e non usa AI.
      </div>

      <div className="growth-audit-form-grid">
        <label className="growth-audit-url-field">
          <span className="growth-audit-url-field__label">Dominio o URL principale</span>
          <input
            type="url"
            className="gcr-input"
            value={rootUrl}
            onChange={(event) => setRootUrlOverride(event.target.value)}
            placeholder="https://tuodominio.it"
          />
          <span className="growth-audit-url-field__hint">
            Inserisci il dominio pubblico visto dagli utenti, non il dominio Shopify admin.
          </span>
        </label>

        <label className="growth-audit-url-field">
          <span className="growth-audit-url-field__label">Pagine massime</span>
          <select
            className="gcr-input"
            value={maxPages}
            onChange={(event) => setMaxPages(Number(event.target.value))}
          >
            {GROWTH_AUDIT_MAX_PAGES_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <button
        type="button"
        className="gcr-btn gcr-btn--primary"
        disabled={isStartDisabled}
        onClick={() => void handleStartAudit()}
      >
        {startRun.isPending ? "Avvio in corso…" : "Avvia scansione sito"}
      </button>

      {startRun.isError && (
        <p className="growth-audit-run-error" role="alert">
          Impossibile avviare la scansione. Verifica l&apos;URL e riprova.
        </p>
      )}

      <p className="growth-audit-full-site__disclaimer">
        La scansione sito copre inventario e controlli tecnici. Il Full Audit professionale
        completo verrà composto progressivamente con Performance, GSC, GA4, Google Ads, GEO e
        CRO.
      </p>
    </>
  );

  const inventorySection = pages.length > 0 && (
    <div
      className={`growth-audit-inventory gcr-card${
        isDashboardMode ? "" : " growth-audit-inventory--secondary"
      }`}
    >
      <div className="growth-audit-inventory__header">
        <div>
          <h4 className="growth-audit-inventory__title">Inventario pagine</h4>
          <p className="growth-audit-inventory__subtitle">
            Tutte le pagine scoperte e scansionate. Usa i filtri se vuoi lavorare manualmente su
            un gruppo specifico.
          </p>
          <p className="growth-audit-inventory__meta">
            {inventoryCounts.total} pagine totali · {filteredPages.length} visibili con filtro
            corrente
          </p>
        </div>
      </div>

      <div className="growth-audit-inventory-filters" role="tablist" aria-label="Filtri tipo pagina">
        {GROWTH_AUDIT_INVENTORY_FILTERS.map((filter) => (
          <button
            key={filter}
            type="button"
            className={`growth-audit-inventory-filter${
              inventoryFilter === filter ? " growth-audit-inventory-filter--active" : ""
            }`}
            onClick={() => setInventoryFilter(filter)}
          >
            {getGrowthAuditInventoryFilterLabel(filter)}
          </button>
        ))}
      </div>

      <div className="growth-audit-inventory-filters growth-audit-inventory-filters--secondary">
        {GROWTH_AUDIT_SCORE_FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            className={`growth-audit-inventory-filter${
              scoreFilter === filter.value ? " growth-audit-inventory-filter--active" : ""
            }`}
            onClick={() => setScoreFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="growth-audit-inventory-filters growth-audit-inventory-filters--secondary">
        {GROWTH_AUDIT_STATUS_FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            className={`growth-audit-inventory-filter${
              statusFilter === filter.value ? " growth-audit-inventory-filter--active" : ""
            }`}
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="growth-audit-pages-table-wrap">
        <table className="growth-audit-pages-table">
          <thead>
            <tr>
              <th>URL</th>
              <th>Tipo</th>
              <th>Fonte</th>
              <th>Shopify</th>
              <th>HTTP</th>
              <th>Score</th>
              <th>Title</th>
              <th>Problemi</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {filteredPages.map((page) => (
              <tr key={page.id} className="growth-audit-pages-table__row">
                <td className="growth-audit-pages-table__url">
                  <div>{page.title || page.url}</div>
                  <div className="growth-audit-pages-table__url-sub">{page.url}</div>
                  {page.status === "failed" && page.errorMessage && (
                    <div className="growth-audit-pages-table__error">{page.errorMessage}</div>
                  )}
                </td>
                <td>{getGrowthAuditPageTypeLabel(page.pageType)}</td>
                <td>
                  <span className={getGrowthAuditSourceBadgeClass(page.source)}>
                    {getGrowthAuditPageSourceLabel(page.source)}
                  </span>
                </td>
                <td>
                  <span
                    className={`growth-audit-pages-table__shopify-badge ${getGrowthAuditShopifyLinkBadgeClass(page)}`}
                  >
                    {getGrowthAuditShopifyLinkBadgeLabel(page)}
                  </span>
                </td>
                <td>{page.httpStatus ?? "—"}</td>
                <td>
                  <span className={getGrowthAuditScoreBadgeClass(page.score)}>
                    {formatGrowthAuditScore(page.score)} {getGrowthAuditPageScoreLabel(page.score)}
                  </span>
                </td>
                <td className="growth-audit-pages-table__title">{page.title ?? "—"}</td>
                <td>{formatPageFindingsCount(findingsByPageId[page.id] ?? 0)}</td>
                <td>{getGrowthAuditPageInventoryStatusLabel(page.status)}</td>
                <td>
                  {resolvedRunId ? (
                    <Link
                      to={APP_ROUTES.projectGrowthAuditPageDetail(
                        projectId,
                        resolvedRunId,
                        page.id,
                      )}
                      className="growth-audit-pages-table__action gcr-btn gcr-btn--secondary gcr-btn--sm"
                    >
                      Gestisci
                    </Link>
                  ) : (
                    <span className="growth-audit-pages-table__action">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const eventsSection = recentEvents.length > 0 && (
    <details
      className="growth-audit-events-disclosure gcr-card"
      open={isRunInProgress}
    >
      <summary className="growth-audit-events-disclosure__summary">
        Eventi e log scansione
      </summary>
      <div className="growth-audit-events growth-audit-events--compact">
        <ul className="growth-audit-events__list">
          {recentEvents.map((event) => (
            <li key={event.id} className="growth-audit-events__item">
              <span className="growth-audit-events__phase">
                {getGrowthAuditPhaseLabel(event.phase)}
              </span>
              <span className="growth-audit-events__message">{event.message}</span>
              {event.progressPercent != null && (
                <span className="growth-audit-events__progress">{event.progressPercent}%</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </details>
  );

  return (
    <motion.div
      className={`growth-audit-page${
        isDashboardMode ? " growth-audit-page--dashboard" : " growth-audit-page--onboarding"
      }`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Growth Audit"
        subtitle={isDashboardMode ? DASHBOARD_SUBTITLE : ONBOARDING_SUBTITLE}
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Growth Audit" },
        ]}
      />

      {isOnboardingMode ? (
        <section className="growth-audit-hero gcr-card gcr-card--glow">
          <h2 className="growth-audit-hero__title">Configura il primo Growth Audit</h2>
          <p className="growth-audit-hero__text">
            Scansiona il sito per creare inventario pagine, score tecnico e priorità operative.
          </p>
          <ol className="growth-audit-flow" aria-label="Flusso Growth Audit">
            {GROWTH_AUDIT_FLOW_STEPS.map((step, index) => (
              <li key={step} className="growth-audit-flow__step">
                <span className="growth-audit-flow__index">{index + 1}</span>
                <span>{step}</span>
                {index < GROWTH_AUDIT_FLOW_STEPS.length - 1 && (
                  <span className="growth-audit-flow__arrow" aria-hidden>
                    →
                  </span>
                )}
              </li>
            ))}
          </ol>
        </section>
      ) : (
        <section className="growth-audit-dashboard-hero gcr-card">
          <div className="growth-audit-dashboard-hero__main">
            <h2 className="growth-audit-dashboard-hero__title">Growth Audit</h2>
            <p className="growth-audit-dashboard-hero__subtitle">{DASHBOARD_SUBTITLE}</p>
          </div>
          {activeRun && (
            <dl className="growth-audit-dashboard-hero__meta">
              {lastScanLabel && (
                <div>
                  <dt>Ultima scansione</dt>
                  <dd>{lastScanLabel}</dd>
                </div>
              )}
              <div>
                <dt>URL analizzato</dt>
                <dd>{getGrowthAuditPublicDomainDisplay(activeRun)}</dd>
              </div>
              <div>
                <dt>Stato run</dt>
                <dd>{getGrowthAuditStatusLabel(activeRun.status)}</dd>
              </div>
            </dl>
          )}
        </section>
      )}

      {showDashboardKpis ? (
        <div className="growth-audit-kpi-grid growth-audit-kpi-grid--dashboard">
          {dashboardKpiItems.map((kpi) => (
            <div key={kpi.label} className="content-seo-kpi gcr-card content-seo-kpi--compact">
              {kpi.label === "Score tecnico" ? (
                <span className={getGrowthAuditScoreBadgeClass(kpi.score)}>{kpi.value}</span>
              ) : (
                <span className="content-seo-kpi__value">{kpi.value}</span>
              )}
              <span className="content-seo-kpi__label">{kpi.label}</span>
              {kpi.meta && <span className="growth-audit-kpi-grid__meta">{kpi.meta}</span>}
            </div>
          ))}
        </div>
      ) : showInventoryKpis ? (
        <div className="growth-audit-kpi-grid growth-audit-kpi-grid--inventory">
          {inventoryKpiItems.map((kpi) => (
            <div key={kpi.label} className="content-seo-kpi gcr-card content-seo-kpi--compact">
              <span className="content-seo-kpi__value">{kpi.value}</span>
              <span className="content-seo-kpi__label">{kpi.label}</span>
            </div>
          ))}
        </div>
      ) : isOnboardingMode ? (
        <div className="growth-audit-kpi-grid">
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">—</span>
            <span className="content-seo-kpi__label">Pagine scoperte</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">—</span>
            <span className="content-seo-kpi__label">Score tecnico</span>
            <span className="growth-audit-kpi-grid__meta">Prossimo step</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">
              {runDetail?.findingsCount ? String(runDetail.findingsCount) : "—"}
            </span>
            <span className="content-seo-kpi__label">Problemi critici</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">
              {runDetail?.tasksCount ? String(runDetail.tasksCount) : "—"}
            </span>
            <span className="content-seo-kpi__label">Task aperti</span>
          </div>
        </div>
      ) : null}

      {showPriorityDashboard && resolvedRunId && (
        <GrowthAuditPriorityDashboard
          projectId={projectId}
          runId={resolvedRunId}
          pages={pages}
          findings={findings}
          tasks={tasks}
          summary={summary}
          siteScore={activeRun?.siteScore}
        />
      )}

      {isOnboardingMode ? (
        <section className="growth-audit-full-site gcr-card">{scanFormFields}</section>
      ) : (
        <details
          className="growth-audit-scan-disclosure gcr-card"
          open={startRun.isPending || undefined}
        >
          <summary className="growth-audit-scan-disclosure__summary">
            <span className="growth-audit-scan-disclosure__title">Nuova scansione sito</span>
            <span className="growth-audit-scan-disclosure__meta">
              Riapri solo se vuoi aggiornare l&apos;inventario o cambiare limite pagine.
            </span>
          </summary>
          <div className="growth-audit-scan-disclosure__content">{scanFormFields}</div>
        </details>
      )}

      {isRunInProgress && activeRun && (
        <div className="growth-audit-run-panel gcr-card">
          <div className="growth-audit-run-panel__header">
            <div>
              <h3 className="growth-audit-run-panel__title">Scansione in corso</h3>
              <p className="growth-audit-run-panel__meta">
                Stato: <strong>{getGrowthAuditStatusLabel(activeRun.status)}</strong>
                {activeRun.phase && (
                  <>
                    {" "}
                    · Fase: <strong>{getGrowthAuditPhaseLabel(activeRun.phase)}</strong>
                  </>
                )}
              </p>
            </div>
            <span className="growth-audit-run-panel__percent">{activeRun.progressPercent}%</span>
          </div>

          <div
            className="growth-audit-progress"
            role="progressbar"
            aria-valuenow={activeRun.progressPercent}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="growth-audit-progress__bar"
              style={{ width: `${activeRun.progressPercent}%` }}
            />
          </div>

          <div className="growth-audit-run-stats">
            <span>Pagine scoperte: {activeRun.pagesDiscovered}</span>
            <span>Classificate: {activeRun.pagesClassified}</span>
            <span>
              Analizzate: {activeRun.pagesAnalyzed}
              {activeRun.totalPages ? ` / ${activeRun.totalPages}` : ""}
            </span>
          </div>

          {activeRun.currentUrl && (
            <p className="growth-audit-run-panel__current">
              URL corrente: <code>{activeRun.currentUrl}</code>
            </p>
          )}

          {summaryMessage && (
            <p className="growth-audit-run-panel__summary">{summaryMessage}</p>
          )}

          {inventoryMessage && (
            <p className="growth-audit-inventory-message">{inventoryMessage}</p>
          )}
        </div>
      )}

      {inventorySection}

      {isDashboardMode && eventsSection}

      {showTechnicalSections && priorityFindings.length > 0 && (
        <details className="growth-audit-findings growth-audit-findings--compact gcr-card">
          <summary className="growth-audit-findings__title">
            Problemi prioritari ({priorityFindings.length})
          </summary>
          <p className="growth-audit-findings__note">
            Vedi anche i cluster ricorrenti nella dashboard sopra.
          </p>
          <ul className="growth-audit-findings__list">
            {priorityFindings.map((finding) => (
              <li key={finding.id} className="growth-audit-findings__item">
                <span className={getGrowthAuditSeverityBadgeClass(finding.severity)}>
                  {finding.severity}
                </span>
                <div className="growth-audit-findings__content">
                  <strong>{finding.title}</strong>
                  {finding.pageId && pageUrlById[finding.pageId] && (
                    <p className="growth-audit-findings__url">{pageUrlById[finding.pageId]}</p>
                  )}
                  {finding.recommendation && (
                    <p className="growth-audit-findings__recommendation">
                      {finding.recommendation}
                    </p>
                  )}
                  {finding.howToValidate && (
                    <p className="growth-audit-findings__validate">
                      Verifica: {finding.howToValidate}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}

      {showTechnicalSections && openTasks.length > 0 && (
        <details className="growth-audit-tasks growth-audit-tasks--compact gcr-card">
          <summary className="growth-audit-tasks__title">Task aperti ({openTasks.length})</summary>
          <ul className="growth-audit-tasks__list">
            {openTasks.map((task) => (
              <li key={task.id} className="growth-audit-tasks__item">
                <div className="growth-audit-tasks__meta">
                  <span className="growth-audit-tasks__priority">{task.priority}</span>
                  <span className="growth-audit-tasks__owner">{task.ownerType}</span>
                </div>
                <strong>{task.title}</strong>
                {task.description && (
                  <p className="growth-audit-tasks__description">{task.description}</p>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}

      {showTechnicalSections && (
        <p className="growth-audit-technical-note">
          La scansione tecnica è deterministica. Per lavorare su una pagina apri Gestisci
          dall&apos;inventario e usa la scheda full-screen.
        </p>
      )}

      <section className="growth-audit-ai-next gcr-card">
        <div className="growth-audit-ai-next__header">
          <h2 className="growth-audit-ai-next__title">Analisi AI/GEO/CRO</h2>
          <span className="growth-audit-ai-next__badge">Disponibile</span>
        </div>
        <p className="growth-audit-ai-next__description">
          Apri Gestisci su una pagina già scansionata per analizzare manualmente le pagine
          prioritarie nella scheda full-screen. Il prompt varia in base al tipo di pagina.
        </p>
        <ul className="growth-audit-ai-next__list">
          {GROWTH_AUDIT_AI_NEXT_BULLETS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="growth-audit-roadmap growth-audit-next-modules gcr-card">
        <h2 className="growth-audit-roadmap__title">Prossimi moduli professionali</h2>
        <ul className="growth-audit-roadmap__list">
          {GROWTH_AUDIT_ROADMAP.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {id && (
          <p className="growth-audit-roadmap__link">
            <Link to={APP_ROUTES.projectContent(id)} className="gcr-btn gcr-btn--secondary gcr-btn--sm">
              Vai a Content SEO
            </Link>
          </p>
        )}
      </section>
    </motion.div>
  );
}
