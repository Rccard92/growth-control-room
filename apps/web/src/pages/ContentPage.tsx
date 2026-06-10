import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const SECTIONS = [
  { title: "PED SEO", description: "Product Experience Document — analisi SEO per prodotto e categoria", icon: "📋" },
  { title: "Idee contenuto AI", description: "Generazione topic e angle basati su dati Search Console e catalogo", icon: "✦" },
  { title: "Bozze blog Shopify", description: "Draft articoli pronti per pubblicazione sul blog dello store", icon: "✎" },
  { title: "Articoli pubblicati", description: "Storico contenuti live con metriche di performance", icon: "📰" },
];

export function ContentPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="SEO Content Room"
        subtitle="Pipeline contenuti AI-driven per il brand"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Contenuti" },
        ]}
      />

      <div className="gcr-grid gcr-grid--2" style={{ marginBottom: "1.5rem" }}>
        {SECTIONS.map((section) => (
          <div key={section.title} className="gcr-card">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
              <span style={{ fontSize: "1.5rem" }}>{section.icon}</span>
              <StatusBadge variant="coming_soon" />
            </div>
            <h3 className="gcr-card__title">{section.title}</h3>
            <p className="gcr-card__description">{section.description}</p>
            <button type="button" className="gcr-btn gcr-btn--secondary" disabled>
              Coming soon
            </button>
          </div>
        ))}
      </div>

      <div className="gcr-card gcr-card--glow">
        <p className="gcr-card__label">Roadmap modulo</p>
        <h3 className="gcr-card__title">Shopify Blog + Google Search Console</h3>
        <p style={{ fontSize: "0.875rem", color: "var(--gcr-text-muted)", margin: 0, lineHeight: 1.7 }}>
          Il modulo Content SEO userà i dati del blog Shopify (via <code>write_content</code>) e le query
          Search Console per generare PED, idee articolo e bozze ottimizzate. Collega Shopify e GSC
          quando disponibili per sbloccare la pipeline completa.
        </p>
      </div>
    </motion.div>
  );
}
