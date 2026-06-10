import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { CommandCard } from "../components/CommandCard";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import {
  countConnectedIntegrations,
  useProject,
  useProjectIntegrations,
} from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

const HEALTH_DATA = [
  { name: "score", value: 72 },
  { name: "gap", value: 28 },
];

export function ProjectOverviewPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project, isLoading } = useProject(id);
  const { data: integrations } = useProjectIntegrations(id);
  const { data: shopifyStatus } = useShopifyStatus(id);

  const connectedCount = integrations ? countConnectedIntegrations(integrations) : 0;
  const shopifyConnected = shopifyStatus?.connected ?? false;

  if (isLoading) {
    return <div className="gcr-skeleton" style={{ height: 200 }} />;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title={project?.name ?? "Control Room"}
        subtitle={project?.description ?? "Panoramica operativa del progetto"}
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "" },
        ]}
      />

      <div className="gcr-grid gcr-grid--3" style={{ marginBottom: "1.5rem" }}>
        <div className="gcr-card gcr-card--glow">
          <p className="gcr-card__label">Health Score</p>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div style={{ width: 80, height: 80 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={HEALTH_DATA}
                    dataKey="value"
                    innerRadius={28}
                    outerRadius={38}
                    startAngle={90}
                    endAngle={-270}
                    stroke="none"
                  >
                    <Cell fill="var(--gcr-accent-violet)" />
                    <Cell fill="var(--gcr-border)" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div>
              <p className="gcr-card__value">72</p>
              <p className="gcr-card__meta">Placeholder — AI analyst in arrivo</p>
            </div>
          </div>
        </div>

        <div className="gcr-card">
          <p className="gcr-card__label">AI Daily Brief</p>
          <p style={{ fontSize: "0.875rem", color: "var(--gcr-text-muted)", margin: "0.5rem 0 0", lineHeight: 1.6 }}>
            Nessun brief generato. Collega integrazioni e sincronizza dati per attivare l&apos;analisi AI giornaliera.
          </p>
        </div>

        <div className="gcr-card">
          <p className="gcr-card__label">Money Leak</p>
          <p className="gcr-card__value" style={{ color: "var(--gcr-warning)" }}>—</p>
          <p className="gcr-card__meta">Rilevamento sprechi ads/inventario — coming soon</p>
        </div>
      </div>

      <div className="gcr-grid gcr-grid--4" style={{ marginBottom: "1.5rem" }}>
        <MetricCard label="Integrazioni attive" value={`${connectedCount}/8`} meta="Provider connessi" />
        <MetricCard
          label="Shopify"
          value={shopifyConnected ? "Connesso" : "Non connesso"}
          meta={shopifyStatus?.shopDomain ?? "OAuth Shopify"}
        />
        <MetricCard label="Contenuti SEO" value="0" meta="Bozze e articoli" />
        <MetricCard label="AI Brief" value="—" meta="Prossima generazione" />
      </div>

      <div className="gcr-card" style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <div>
            <h3 className="gcr-card__title">Shopify</h3>
            <p className="gcr-card__description" style={{ margin: 0 }}>
              Store e-commerce — ordini, prodotti, inventario
            </p>
          </div>
          <StatusBadge variant={shopifyConnected ? "connected" : "not_connected"} />
        </div>
        <Link
          to={shopifyConnected ? APP_ROUTES.projectShopify(id!) : APP_ROUTES.projectShopifyConnect(id!)}
          className="gcr-btn gcr-btn--secondary"
        >
          {shopifyConnected ? "Apri Shopify Control Room" : "Connetti Shopify"}
        </Link>
      </div>

      <h2 style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--gcr-text-dim)", marginBottom: "1rem" }}>
        Shortcuts
      </h2>
      <div className="gcr-grid gcr-grid--4">
        <CommandCard icon="⬡" label="Integration Center" description="Connettori e grafo dati" to={APP_ROUTES.projectIntegrations(id!)} />
        <CommandCard icon="🛍" label="Shopify" description="Store, ordini, KPI" to={APP_ROUTES.projectShopify(id!)} />
        <CommandCard icon="✎" label="Content SEO" description="PED, bozze blog, idee AI" to={APP_ROUTES.projectContent(id!)} />
        <CommandCard icon="✦" label="AI Brief" description="Insight e azioni consigliate" to={APP_ROUTES.projectAiBrief(id!)} />
      </div>
    </motion.div>
  );
}
