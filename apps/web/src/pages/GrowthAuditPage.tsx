import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { SeoSkillLibrary } from "../components/seo-skills";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

const GROWTH_AUDIT_FLOW_STEPS = [
  "Scansiona sito",
  "Classifica pagine",
  "Analizza priorità",
  "Correggi e riscansiona",
] as const;

const GROWTH_AUDIT_KPI_PLACEHOLDERS = [
  { label: "Site Score", value: "—" },
  { label: "Pagine scoperte", value: "—" },
  { label: "Problemi critici", value: "—" },
  { label: "Task aperti", value: "—" },
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
          Il Growth Audit sarà il centro operativo per capire lo stato del sito, trovare problemi
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
        {GROWTH_AUDIT_KPI_PLACEHOLDERS.map((kpi) => (
          <div key={kpi.label} className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">{kpi.value}</span>
            <span className="content-seo-kpi__label">{kpi.label}</span>
            <span className="growth-audit-kpi-grid__meta">Non ancora disponibile</span>
          </div>
        ))}
      </div>

      <section className="growth-audit-placeholder-card gcr-card">
        <div className="growth-audit-placeholder-card__header">
          <div>
            <h2 className="growth-audit-placeholder-card__title">Full Site Audit</h2>
            <p className="growth-audit-placeholder-card__description">
              Scansiona il sito, classifica homepage, prodotti, categorie, articoli e landing, poi
              applica analisi diverse in base al tipo di pagina.
            </p>
          </div>
          <span className="growth-audit-placeholder-card__badge">In preparazione</span>
        </div>
        <p className="growth-audit-placeholder-card__note">
          Il crawl multi-pagina arriverà nello step successivo. In questa fase puoi già eseguire
          audit guidati su singole URL.
        </p>
        <button type="button" className="gcr-btn gcr-btn--secondary" disabled>
          Prepara Full Audit
        </button>
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
