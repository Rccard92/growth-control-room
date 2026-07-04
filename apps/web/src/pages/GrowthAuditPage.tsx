import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import type { GrowthAuditInventoryFilter } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { SeoSkillLibrary } from "../components/seo-skills";
import {
  useGrowthAuditRun,
  useGrowthAuditRuns,
  useStartGrowthAuditRun,
} from "../hooks/useGrowthAudit";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import {
  GROWTH_AUDIT_INVENTORY_FILTERS,
  GROWTH_AUDIT_MAX_PAGES_OPTIONS,
  aggregatePageInventory,
  filterInventoryPages,
  getDefaultRootUrl,
  getGrowthAuditInventoryFilterLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageStatusLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditStatusLabel,
  getInventoryKpiItems,
  getInventoryMessage,
} from "../lib/growth-audit-utils";
import { APP_ROUTES } from "../routes/config";

const GROWTH_AUDIT_FLOW_STEPS = [
  "Scansiona sito",
  "Classifica pagine",
  "Analizza priorità",
  "Correggi e riscansiona",
] as const;

const GROWTH_AUDIT_ROADMAP = [
  "Analisi tecnica e AI per tipologia di pagina",
  "Dashboard priorità e scoring pagina",
  "Rescan singola pagina",
  "Integrazioni: PageSpeed, Search Console, GA4, Google Ads, Firecrawl/DataForSEO",
] as const;

export function GrowthAuditPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: shopifyStatus } = useShopifyStatus(id);
  const { data: runs } = useGrowthAuditRuns(projectId);
  const startRun = useStartGrowthAuditRun(projectId);

  const defaultRootUrl = useMemo(
    () => getDefaultRootUrl(shopifyStatus?.shopDomain),
    [shopifyStatus?.shopDomain],
  );
  const [rootUrlOverride, setRootUrlOverride] = useState<string | null>(null);
  const rootUrl = rootUrlOverride ?? defaultRootUrl;
  const [maxPages, setMaxPages] = useState<number>(50);
  const [inventoryFilter, setInventoryFilter] = useState<GrowthAuditInventoryFilter>("all");
  const [activeRunId, setActiveRunId] = useState<string | undefined>();

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

  const activeRun = runDetail?.run;
  const pages = runDetail?.pages ?? [];
  const events = runDetail?.events ?? [];
  const recentEvents = [...events].reverse().slice(0, 5);
  const summary = activeRun?.summary ?? null;
  const summaryMessage = typeof summary?.message === "string" ? summary.message : null;
  const inventoryMessage = getInventoryMessage(activeRun?.pagesDiscovered ?? 0, summary);
  const filteredPages = useMemo(
    () => filterInventoryPages(pages, inventoryFilter),
    [pages, inventoryFilter],
  );
  const inventoryCounts = useMemo(() => aggregatePageInventory(pages), [pages]);
  const inventoryKpiItems = useMemo(
    () => getInventoryKpiItems(pages, summary),
    [pages, summary],
  );
  const showInventoryKpis = activeRun?.status === "completed" && pages.length > 0;

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

      {showInventoryKpis ? (
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
              Scopre URL da sitemap e dati Shopify sincronizzati, classifica le pagine e crea
              l&apos;inventario operativo del sito.
            </p>
          </div>
        </div>

        <div className="growth-audit-skeleton-banner">
          Discovery attiva: sitemap XML, sitemap index e URL Shopify già sincronizzati. L&apos;analisi
          AI per pagina arriverà nel prossimo step.
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
              <span>Analizzate: {activeRun.pagesAnalyzed}</span>
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

                <div className="growth-audit-pages-table-wrap">
                  <table className="growth-audit-pages-table">
                    <thead>
                      <tr>
                        <th>URL</th>
                        <th>Tipo</th>
                        <th>Fonte</th>
                        <th>Stato</th>
                        <th>Score</th>
                        <th>Azione</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPages.map((page) => (
                        <tr key={page.id}>
                          <td className="growth-audit-pages-table__url">
                            <div>{page.title || page.url}</div>
                            <div className="growth-audit-pages-table__url-sub">{page.url}</div>
                          </td>
                          <td>{getGrowthAuditPageTypeLabel(page.pageType)}</td>
                          <td>
                            <span className={getGrowthAuditSourceBadgeClass(page.source)}>
                              {getGrowthAuditPageSourceLabel(page.source)}
                            </span>
                          </td>
                          <td>{getGrowthAuditPageStatusLabel(page.status)}</td>
                          <td>{page.score ?? "—"}</td>
                          <td>
                            <span className="growth-audit-action-placeholder">Analisi in arrivo</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="growth-audit-manual-section">
        <header className="growth-audit-manual-section__header">
          <h2 className="growth-audit-manual-section__title">Audit guidato su URL</h2>
          <p className="growth-audit-manual-section__description">
            Modalità complementare per analizzare subito una pagina specifica mentre l&apos;inventario
            full site viene costruito.
          </p>
        </header>
        <SeoSkillLibrary projectId={projectId} />
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
