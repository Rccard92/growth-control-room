import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { SeoOptimizerRoom } from "../components/content/optimizer/SeoOptimizerRoom";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

export function ContentPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: shopifyStatus } = useShopifyStatus(id);
  const connected = shopifyStatus?.connected ?? false;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Product & Collection SEO Optimizer"
        subtitle="Analisi e proposte SEO per prodotti e categorie Shopify"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Contenuti" },
        ]}
      />

      {!connected && (
        <div className="gcr-card gcr-card--glow" style={{ marginBottom: "1.5rem" }}>
          <p className="gcr-card__label">Shopify richiesto</p>
          <h3 className="gcr-card__title">Collega Shopify per iniziare</h3>
          <p className="gcr-card__description">
            Sincronizza prodotti (Sync v2) e categorie, poi analizza e genera proposte SEO revisionabili.
          </p>
          {id && (
            <Link to={APP_ROUTES.projectIntegrations(id)} className="gcr-btn gcr-btn--primary">
              Vai alle integrazioni
            </Link>
          )}
        </div>
      )}

      {connected && <SeoOptimizerRoom projectId={projectId} connected={connected} />}
    </motion.div>
  );
}
