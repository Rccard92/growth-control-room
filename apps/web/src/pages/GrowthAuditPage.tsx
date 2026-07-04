import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
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
  getDefaultRootUrl,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageStatusLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditStatusLabel,
} from "../lib/growth-audit-utils";
import { APP_ROUTES } from "../routes/config";

const GROWTH_AUDIT_FLOW_STEPS = [
  "Scansiona sito",
  "Classifica pagine",
  "Analizza priorità",
  "Correggi e riscansiona",
] as const;

const GROWTH_AUDIT_ROADMAP = [
  "Crawler sitemap e Shopify URL discovery",
  "Classificazione automatica pagine",
  "Full Site Audit con progress bar",
  "Dashboard pagine e priorità",
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
  const summaryMessage =
    typeof activeRun?.summary?.message === "string" ? activeRun.summary.message : null;

  const kpiItems = [
    {
      label: "Site Score",
      value: activeRun?.siteScore != null ? String(activeRun.siteScore) : "—",
      meta: activeRun?.siteScore != null ? "Da run attiva" : "Non ancora disponibile",
    },
    {
      label: "Pagine scoperte",
      value: activeRun ? String(activeRun.pagesDiscovered) : "—",
      meta: activeRun ? "Aggiornato dalla run" : "Non ancora disponibile",
    },
    {
      label: "Problemi critici",
      value: runDetail?.findingsCount ? String(runDetail.findingsCount) : "—",
      meta: runDetail?.findingsCount ? "Finding registrati" : "Non ancora disponibile",
    },
    {
      label: "Task aperti",
      value: runDetail?.tasksCount ? String(runDetail.tasksCount) : "—",
      meta: runDetail?.tasksCount ? "Task registrati" : "Non ancora disponibile",
    },
  ];

  const handleStartAudit = async () => {
    const trimmed = rootUrl.trim();
    if (!trimmed) return;

    const response = await startRun.mutateAsync({
      rootUrl: trimmed,
      provider: "openai",
      auditMode: "full_site_mvp",
      maxPages: 50,
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

      <div className="growth-audit-kpi-grid">
        {kpiItems.map((kpi) => (
          <div key={kpi.label} className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">{kpi.value}</span>
            <span className="content-seo-kpi__label">{kpi.label}</span>
            <span className="growth-audit-kpi-grid__meta">{kpi.meta}</span>
          </div>
        ))}
      </div>

      <section className="growth-audit-full-site gcr-card">
        <div className="growth-audit-full-site__header">
          <div>
            <h2 className="growth-audit-full-site__title">Full Site Audit</h2>
            <p className="growth-audit-full-site__description">
              Scansiona il sito, classifica homepage, prodotti, categorie, articoli e landing, poi
              applica analisi diverse in base al tipo di pagina.
            </p>
          </div>
        </div>

        <div className="growth-audit-skeleton-banner">
          Nel prossimo step abiliteremo discovery sitemap e crawl multi-pagina. In questa fase la run
          crea una pagina seed e la classifica automaticamente.
        </div>

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

            {recentEvents.length > 0 && (
              <div className="growth-audit-events">
                <h4 className="growth-audit-events__title">Ultimi eventi</h4>
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
              <div className="growth-audit-pages-table-wrap">
                <h4 className="growth-audit-pages-table__title">Pagine</h4>
                <table className="growth-audit-pages-table">
                  <thead>
                    <tr>
                      <th>URL</th>
                      <th>Tipo</th>
                      <th>Stato</th>
                      <th>Fonte</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pages.map((page) => (
                      <tr key={page.id}>
                        <td className="growth-audit-pages-table__url">{page.url}</td>
                        <td>{getGrowthAuditPageTypeLabel(page.pageType)}</td>
                        <td>{getGrowthAuditPageStatusLabel(page.status)}</td>
                        <td>{getGrowthAuditPageSourceLabel(page.source)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="growth-audit-manual-section">
        <header className="growth-audit-manual-section__header">
          <h2 className="growth-audit-manual-section__title">Audit guidato su URL</h2>
          <p className="growth-audit-manual-section__description">
            Usa questa modalità per analizzare subito una pagina specifica mentre prepariamo il full
            site audit.
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
