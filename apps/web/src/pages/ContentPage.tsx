import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { ContentSeoEditorialRoom } from "../components/content/editorial/ContentSeoEditorialRoom";
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
    <motion.div
      className="content-seo-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Content SEO"
        subtitle="Pianifica blog, ricette, brief editoriali e contenuti SEO. L'ottimizzazione di prodotti e categorie Shopify ora vive in Growth Audit."
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Content SEO" },
        ]}
      />

      <div className="gcr-card content-seo-audit-redirect-card">
        <h3 className="gcr-card__title">Prodotti e categorie si ottimizzano in Growth Audit</h3>
        <p className="gcr-card__description">
          Per analizzare, correggere e riscansionare pagine prodotto e collection Shopify usa il
          Growth Audit. Content SEO resta dedicato alla produzione editoriale.
        </p>
        {id && (
          <Link
            to={APP_ROUTES.projectGrowthAudit(id)}
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
          >
            Apri Growth Audit
          </Link>
        )}
      </div>

      <ContentSeoEditorialRoom projectId={projectId} shopifyConnected={connected} />
    </motion.div>
  );
}
