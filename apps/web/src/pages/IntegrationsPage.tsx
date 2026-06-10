import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import { INTEGRATIONS } from "@gcr/shared";
import { IntegrationCard } from "../components/IntegrationCard";
import { IntegrationGraph } from "../components/IntegrationGraph";
import { PageHeader } from "../components/PageHeader";
import { useProject, useProjectIntegrations } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

export function IntegrationsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);
  const { data: integrations, isLoading, error } = useProjectIntegrations(id);

  const statusMap = new Map(
    (integrations ?? []).map((i) => [i.provider, i.status]),
  );

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Integration Center"
        subtitle="Collega le piattaforme e-commerce e marketing al progetto"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Integrazioni" },
        ]}
      />

      {isLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}
      {error && (
        <div className="gcr-alert gcr-alert--error">{error.message}</div>
      )}

      <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "2rem" }}>
        {INTEGRATIONS.map((meta) => {
          const isShopify = meta.provider === "shopify";
          const apiStatus = statusMap.get(meta.provider);

          if (isShopify) {
            const connected = apiStatus === "connected";
            return (
              <IntegrationCard
                key={meta.provider}
                meta={meta}
                status={apiStatus ?? "not_connected"}
                href={
                  connected
                    ? APP_ROUTES.projectShopify(id!)
                    : APP_ROUTES.projectShopifyConnect(id!)
                }
                actionLabel={connected ? "Gestisci" : "Connetti"}
              />
            );
          }

          return (
            <IntegrationCard
              key={meta.provider}
              meta={meta}
              status="coming_soon"
              actionLabel="Coming soon"
              disabled
            />
          );
        })}
      </div>

      <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--gcr-text)", marginBottom: "1rem" }}>
        Integration Graph
      </h2>
      <p style={{ fontSize: "0.8125rem", color: "var(--gcr-text-muted)", marginBottom: "1rem" }}>
        Vista relazionale del progetto e dei connettori. Shopify è il primo provider attivo.
      </p>
      {integrations && (
        <IntegrationGraph
          projectName={project?.name ?? "Progetto"}
          integrations={integrations}
        />
      )}
    </motion.div>
  );
}
