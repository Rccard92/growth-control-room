import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { ContentSeoCollectionOpportunitiesPanel } from "../components/content/ContentSeoCollectionOpportunitiesPanel";
import { ContentSeoHeader } from "../components/content/ContentSeoHeader";
import { ContentSeoInternalLinkingPanel } from "../components/content/ContentSeoInternalLinkingPanel";
import { ContentSeoIssuesPanel } from "../components/content/ContentSeoIssuesPanel";
import { ContentSeoKpiStrip } from "../components/content/ContentSeoKpiStrip";
import { ContentSeoOpportunitiesPanel } from "../components/content/ContentSeoOpportunitiesPanel";
import { ContentSeoProductOpportunitiesPanel } from "../components/content/ContentSeoProductOpportunitiesPanel";
import {
  useContentSeoAnalyze,
  useContentSeoDashboard,
  useContentSeoSync,
} from "../hooks/useContentSeo";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

function ContentSeoSkeleton() {
  return (
    <div className="content-seo-skeleton-grid">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="gcr-skeleton content-seo-skeleton-card" />
      ))}
    </div>
  );
}

export function ContentPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: shopifyStatus } = useShopifyStatus(id);
  const connected = shopifyStatus?.connected ?? false;

  const {
    data: dashboard,
    isLoading,
    error,
  } = useContentSeoDashboard(projectId, connected);

  const syncMutation = useContentSeoSync(projectId);
  const analyzeMutation = useContentSeoAnalyze(projectId);

  const showEmpty =
    connected &&
    !isLoading &&
    !(dashboard?.summary.hasSyncedContent) &&
    (dashboard?.summary.totalIssues ?? 0) === 0 &&
    (dashboard?.summary.contentOpportunities ?? 0) === 0;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Content SEO Room"
        subtitle="Audit SEO e opportunità contenuto da Shopify"
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
            Il Content SEO Engine sincronizza collections, pagine, blog e articoli via scope{" "}
            <code>read_content</code>.
          </p>
          {id && (
            <Link to={APP_ROUTES.projectIntegrations(id)} className="gcr-btn gcr-btn--primary">
              Vai alle integrazioni
            </Link>
          )}
        </div>
      )}

      {connected && (
        <>
          <ContentSeoHeader
            onSync={() => syncMutation.mutate()}
            onAnalyze={() => analyzeMutation.mutate()}
            syncLoading={syncMutation.isPending}
            analyzeLoading={analyzeMutation.isPending}
            shopifyConnected={connected}
          />

          {(syncMutation.isSuccess || analyzeMutation.isSuccess) && (
            <div className="content-seo-banner content-seo-banner--success">
              {syncMutation.isSuccess &&
                `Sync completato: ${syncMutation.data.collectionsSynced} collections, ${syncMutation.data.pagesSynced} pagine, ${syncMutation.data.blogsSynced} blog, ${syncMutation.data.articlesSynced} articoli.`}
              {analyzeMutation.isSuccess &&
                ` Analisi: ${analyzeMutation.data.issuesCreated} issues, ${analyzeMutation.data.opportunitiesCreated} opportunità.`}
            </div>
          )}

          {(syncMutation.isError || analyzeMutation.isError || error) && (
            <div className="content-seo-banner content-seo-banner--error">
              {syncMutation.error instanceof Error
                ? syncMutation.error.message
                : analyzeMutation.error instanceof Error
                  ? analyzeMutation.error.message
                  : error instanceof Error
                    ? error.message
                    : "Errore durante l'operazione"}
            </div>
          )}

          {isLoading && <ContentSeoSkeleton />}

          {showEmpty && (
            <div className="gcr-card content-seo-empty">
              <h3 className="gcr-card__title">Sincronizza i contenuti Shopify per iniziare</h3>
              <p className="gcr-card__description">
                Usa il pulsante sopra per importare collections, pagine, blog e articoli. Poi esegui
                Analizza SEO.
              </p>
            </div>
          )}

          {dashboard && !isLoading && !showEmpty && (
            <>
              <ContentSeoKpiStrip summary={dashboard.summary} />

              <div className="content-seo-grid">
                <ContentSeoIssuesPanel issues={dashboard.issues} />
                <ContentSeoOpportunitiesPanel opportunities={dashboard.opportunities} />
                <ContentSeoProductOpportunitiesPanel
                  opportunities={dashboard.topProductOpportunities}
                />
                <ContentSeoCollectionOpportunitiesPanel
                  opportunities={dashboard.topCollectionOpportunities}
                />
                <ContentSeoInternalLinkingPanel
                  opportunities={dashboard.internalLinkingOpportunities}
                />
              </div>
            </>
          )}
        </>
      )}
    </motion.div>
  );
}
