import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import type {
  GrowthAuditInventoryFilter,
  GrowthAuditPageStatusFilter,
  GrowthAuditScoreFilter,
} from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { GrowthAuditPageDrawer } from "../components/growth-audit/GrowthAuditPageDrawer";
import {
  useGrowthAuditFindings,
  useGrowthAuditRun,
  useGrowthAuditRuns,
  useGrowthAuditTasks,
  useRescanGrowthAuditPage,
  useStartGrowthAuditRun,
} from "../hooks/useGrowthAudit";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
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
  getFindingsForPage,
  getGrowthAuditInventoryFilterLabel,
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditSeverityBadgeClass,
  getGrowthAuditShopifyLinkBadgeClass,
  getGrowthAuditShopifyLinkBadgeLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditStatusLabel,
  getInventoryKpiItems,
  getInventoryMessage,
  getTasksForPage,
  getTechnicalKpiItems,
  getTopOpenTasks,
  getTopPriorityFindings,
  sortGrowthAuditFindings,
  sortGrowthAuditTasks,
} from "../lib/growth-audit-utils";
import { APP_ROUTES } from "../routes/config";

const GROWTH_AUDIT_FLOW_STEPS = [
  "Scansiona sito",
  "Classifica pagine",
  "Analizza priorità",
  "Correggi e riscansiona",
] as const;

const GROWTH_AUDIT_ROADMAP = [
  "Analisi AI/GEO/CRO per pagine prioritarie",
  "Batch AI controllato su pagine ad alto impatto",
  "Integrazioni: PageSpeed, Search Console, GA4, Google Ads, Firecrawl/DataForSEO",
] as const;

const GROWTH_AUDIT_AI_NEXT_BULLETS = [
  "Prodotto: SEO ecommerce, schema Product, immagini, CRO e trust.",
  "Blog: contenuto, intent, E-E-A-T, GEO e linking interno.",
  "Collection: intent commerciale, schema, testo categoria e UX catalogo.",
] as const;

export function GrowthAuditPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: shopifyStatus } = useShopifyStatus(id);
  const { data: runs } = useGrowthAuditRuns(projectId);
  const startRun = useStartGrowthAuditRun(projectId);
  const rescanPage = useRescanGrowthAuditPage(projectId);

  const defaultRootUrl = useMemo(
    () => getDefaultRootUrl(shopifyStatus?.shopDomain),
    [shopifyStatus?.shopDomain],
  );
  const [rootUrlOverride, setRootUrlOverride] = useState<string | null>(null);
  const rootUrl = rootUrlOverride ?? defaultRootUrl;
  const [maxPages, setMaxPages] = useState<number>(50);
  const [inventoryFilter, setInventoryFilter] = useState<GrowthAuditInventoryFilter>("all");
  const [scoreFilter, setScoreFilter] = useState<GrowthAuditScoreFilter>("all");
  const [statusFilter, setStatusFilter] = useState<GrowthAuditPageStatusFilter>("all");
  const [activeRunId, setActiveRunId] = useState<string | undefined>();
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);

  useEffect(() => {
    setSelectedPageId(null);
  }, [activeRunId]);

  useEffect(() => {
    if (activeRunId) return;
    const latest = runs?.[0];
    if (latest && latest.status !== "completed" && latest.status !== "failed") {
      setActiveRunId(latest.id);
    } else if (latest?.status === "completed") {
      setActiveRunId(latest.id);
    }
  }, [runs, activeRunId]);

  const { data: runDetail } = useGrowthAuditRun(projectId, activeRunId, Boolean(activeRunId));
  const runStatus = runDetail?.run.status;
  const { data: findings = [] } = useGrowthAuditFindings(
    projectId,
    activeRunId,
    undefined,
    runStatus,
    Boolean(activeRunId),
  );
  const { data: tasks = [] } = useGrowthAuditTasks(
    projectId,
    activeRunId,
    { status: "open" },
    runStatus,
    Boolean(activeRunId),
  );

  const activeRun = runDetail?.run;
  const pages = runDetail?.pages ?? [];
  const events = runDetail?.events ?? [];
  const recentEvents = [...events].reverse().slice(0, 5);
  const summary = activeRun?.summary ?? null;
  const summaryMessage = typeof summary?.message === "string" ? summary.message : null;
  const inventoryMessage = getInventoryMessage(activeRun?.pagesDiscovered ?? 0, summary);
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
  const technicalKpiItems = useMemo(
    () =>
      getTechnicalKpiItems(activeRun, runDetail?.findingsCount, runDetail?.tasksCount),
    [activeRun, runDetail?.findingsCount, runDetail?.tasksCount],
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
  const selectedPage = useMemo(
    () => pages.find((page) => page.id === selectedPageId) ?? null,
    [pages, selectedPageId],
  );
  const selectedPageFindings = useMemo(
    () => sortGrowthAuditFindings(getFindingsForPage(findings, selectedPageId)),
    [findings, selectedPageId],
  );
  const selectedPageTasks = useMemo(
    () => sortGrowthAuditTasks(getTasksForPage(tasks, selectedPageId)),
    [tasks, selectedPageId],
  );

  useEffect(() => {
    if (!selectedPageId) return;
    if (!pages.some((page) => page.id === selectedPageId)) {
      setSelectedPageId(null);
    }
  }, [pages, selectedPageId]);

  const showInventoryKpis =
    activeRun?.status === "completed" &&
    pages.length > 0 &&
    !activeRun.siteScore &&
    !summary?.averageTechnicalScore;
  const showTechnicalKpis =
    Boolean(activeRun?.siteScore != null || summary?.averageTechnicalScore != null) ||
    activeRun?.status === "analyzing" ||
    activeRun?.status === "partial_failed";
  const showTechnicalSections =
    activeRun?.status === "completed" ||
    activeRun?.status === "partial_failed" ||
    activeRun?.status === "analyzing";

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

  return (
    <motion.div
      className="growth-audit-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Growth Audit"
        subtitle="Analizza sito, pagine, contenuti, SEO, GEO, CRO e priorità operative per aumentare performance organiche e ritorno ads."
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Growth Audit" },
        ]}
      />

      <section className="growth-audit-hero gcr-card gcr-card--glow">
        <p className="growth-audit-hero__text">
          Il Growth Audit è il centro operativo per capire lo stato del sito, trovare problemi
          prioritari e guidare le correzioni pagina per pagina.
        </p>
        {shopifyStatus?.connected && shopifyStatus.shopDomain && (
          <p className="growth-audit-hero__domain">
            Dominio rilevato: <strong>{shopifyStatus.shopDomain}</strong>
          </p>
        )}
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

      {showTechnicalKpis ? (
        <div className="growth-audit-kpi-grid">
          {technicalKpiItems.map((kpi) => (
            <div key={kpi.label} className="content-seo-kpi gcr-card content-seo-kpi--compact">
              {kpi.label === "Site Score" ? (
                <span className={getGrowthAuditScoreBadgeClass(kpi.score)}>
                  {kpi.value}
                </span>
              ) : (
                <span className="content-seo-kpi__value">{kpi.value}</span>
              )}
              <span className="content-seo-kpi__label">{kpi.label}</span>
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
      ) : (
        <div className="growth-audit-kpi-grid">
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">
              {activeRun ? String(activeRun.pagesDiscovered) : "—"}
            </span>
            <span className="content-seo-kpi__label">Pagine scoperte</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">—</span>
            <span className="content-seo-kpi__label">Site Score</span>
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
      )}

      <section className="growth-audit-full-site gcr-card">
        <div className="growth-audit-full-site__header">
          <div>
            <h2 className="growth-audit-full-site__title">Full Site Audit</h2>
            <p className="growth-audit-full-site__description">
              Scopre URL da sitemap e dati Shopify sincronizzati, classifica le pagine e avvia
              la scansione tecnica deterministica.
            </p>
          </div>
        </div>

        <div className="growth-audit-skeleton-banner">
          Scansione tecnica attiva: title, meta, canonical, H1, schema, immagini e link.
          Questa scansione è deterministica e non usa AI.
        </div>

        <div className="growth-audit-form-grid">
          <label className="growth-audit-url-field">
            <span className="growth-audit-url-field__label">Dominio o URL principale</span>
            <input
              type="url"
              className="gcr-input"
              value={rootUrl}
              onChange={(event) => setRootUrlOverride(event.target.value)}
              placeholder="https://example.com"
            />
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
          {startRun.isPending ? "Avvio in corso…" : "Avvia Full Site Audit"}
        </button>

        {startRun.isError && (
          <p className="growth-audit-run-error" role="alert">
            Impossibile avviare l&apos;audit. Verifica l&apos;URL e riprova.
          </p>
        )}

        {activeRun && (
          <div className="growth-audit-run-panel">
            <div className="growth-audit-run-panel__header">
              <div>
                <h3 className="growth-audit-run-panel__title">Run attiva</h3>
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

            {recentEvents.length > 0 && (
              <div className="growth-audit-events growth-audit-events--compact">
                <h4 className="growth-audit-events__title">Eventi recenti</h4>
                <ul className="growth-audit-events__list">
                  {recentEvents.map((event) => (
                    <li key={event.id} className="growth-audit-events__item">
                      <span className="growth-audit-events__phase">
                        {getGrowthAuditPhaseLabel(event.phase)}
                      </span>
                      <span className="growth-audit-events__message">{event.message}</span>
                      {event.progressPercent != null && (
                        <span className="growth-audit-events__progress">
                          {event.progressPercent}%
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {pages.length > 0 && (
              <div className="growth-audit-inventory">
                <div className="growth-audit-inventory__header">
                  <div>
                    <h4 className="growth-audit-inventory__title">Inventario pagine</h4>
                    <p className="growth-audit-inventory__subtitle">
                      {inventoryCounts.total} pagine totali · {filteredPages.length} visibili con
                      filtro corrente
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
                        <tr
                          key={page.id}
                          className="growth-audit-pages-table__row--clickable"
                          onClick={() => setSelectedPageId(page.id)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              setSelectedPageId(page.id);
                            }
                          }}
                          role="button"
                          tabIndex={0}
                          aria-label={`Apri dettaglio pagina ${page.url}`}
                        >
                          <td className="growth-audit-pages-table__url">
                            <div>{page.title || page.url}</div>
                            <div className="growth-audit-pages-table__url-sub">{page.url}</div>
                            {page.status === "failed" && page.errorMessage && (
                              <div className="growth-audit-pages-table__error">
                                {page.errorMessage}
                              </div>
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
                              {formatGrowthAuditScore(page.score)}{" "}
                              {getGrowthAuditPageScoreLabel(page.score)}
                            </span>
                          </td>
                          <td className="growth-audit-pages-table__title">
                            {page.title ?? "—"}
                          </td>
                          <td>
                            {formatPageFindingsCount(findingsByPageId[page.id] ?? 0)}
                          </td>
                          <td>{getGrowthAuditPageInventoryStatusLabel(page.status)}</td>
                          <td>
                            <button
                              type="button"
                              className="growth-audit-pages-table__action gcr-btn gcr-btn--secondary gcr-btn--sm"
                              onClick={(event) => {
                                event.stopPropagation();
                                setSelectedPageId(page.id);
                              }}
                            >
                              Dettaglio
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {showTechnicalSections && priorityFindings.length > 0 && (
              <section className="growth-audit-findings gcr-card">
                <h4 className="growth-audit-findings__title">Problemi prioritari</h4>
                <ul className="growth-audit-findings__list">
                  {priorityFindings.map((finding) => (
                    <li key={finding.id} className="growth-audit-findings__item">
                      <span className={getGrowthAuditSeverityBadgeClass(finding.severity)}>
                        {finding.severity}
                      </span>
                      <div className="growth-audit-findings__content">
                        <strong>{finding.title}</strong>
                        {finding.pageId && pageUrlById[finding.pageId] && (
                          <p className="growth-audit-findings__url">
                            {pageUrlById[finding.pageId]}
                          </p>
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
              </section>
            )}

            {showTechnicalSections && openTasks.length > 0 && (
              <section className="growth-audit-tasks gcr-card">
                <h4 className="growth-audit-tasks__title">Task aperti</h4>
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
              </section>
            )}

            {showTechnicalSections && (
              <p className="growth-audit-technical-note">
                La scansione tecnica è deterministica. Per SEO/GEO/CRO avanzato apri una pagina
                analizzata e usa la tab AI/GEO/CRO nel drawer.
              </p>
            )}
          </div>
        )}
      </section>

      <GrowthAuditPageDrawer
        open={Boolean(selectedPage)}
        page={selectedPage}
        findings={selectedPageFindings}
        tasks={selectedPageTasks}
        projectId={projectId}
        runId={activeRunId}
        runStatus={activeRun?.status}
        isRescanning={rescanPage.isPending}
        onRescan={async ({ runId, pageId, clearPreviousOpenItems }) => {
          await rescanPage.mutateAsync({
            runId,
            pageId,
            payload: { clearPreviousOpenItems },
          });
        }}
        onClose={() => setSelectedPageId(null)}
      />

      <section className="growth-audit-ai-next gcr-card">
        <div className="growth-audit-ai-next__header">
          <h2 className="growth-audit-ai-next__title">Analisi AI/GEO/CRO</h2>
          <span className="growth-audit-ai-next__badge">Disponibile</span>
        </div>
        <p className="growth-audit-ai-next__description">
          Apri una pagina già scansionata e usa la tab AI/GEO/CRO nel drawer per analizzare
          manualmente le pagine prioritarie. Il prompt varia in base al tipo di pagina.
        </p>
        <ul className="growth-audit-ai-next__list">
          {GROWTH_AUDIT_AI_NEXT_BULLETS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="growth-audit-roadmap gcr-card">
        <h2 className="growth-audit-roadmap__title">Prossimi step</h2>
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
