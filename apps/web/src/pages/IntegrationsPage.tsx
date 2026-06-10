import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  INTEGRATION_BY_PROVIDER,
  INTEGRATIONS,
  type Integration,
  type IntegrationStatus,
} from "@gcr/shared";
import { Button, Card, PageHeader } from "@gcr/ui";
import { apiFetch } from "../lib/api";

const STATUS_LABELS: Record<IntegrationStatus, string> = {
  not_connected: "Non connessa",
  connected: "Connessa",
  error: "Errore",
};

export function IntegrationsPage() {
  const { id } = useParams<{ id: string }>();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    apiFetch<Integration[]>(`/api/projects/${id}/integrations`)
      .then(setIntegrations)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const statusByProvider = useMemo(
    () => new Map(integrations.map((integration) => [integration.provider, integration.status])),
    [integrations],
  );

  return (
    <>
      <PageHeader
        title="Integrazioni"
        subtitle="Collega le piattaforme e-commerce e marketing"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "Integrazioni" },
        ]}
      />
      {loading && (
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>Caricamento integrazioni…</p>
      )}
      {error && (
        <p style={{ color: "#dc2626", fontSize: "0.875rem" }}>
          Errore nel caricamento: {error}
        </p>
      )}
      <div className="placeholder-grid">
        {INTEGRATIONS.map((integration) => {
          const status = statusByProvider.get(integration.provider) ?? "not_connected";
          const meta = INTEGRATION_BY_PROVIDER[integration.provider];

          return (
            <Card key={integration.provider} title={meta.label} description={meta.description}>
              <div className="integration-card">
                <div className="integration-card__header">
                  <span className="integration-card__icon">{meta.icon}</span>
                  <span className="integration-card__status">{STATUS_LABELS[status]}</span>
                </div>
                {integration.provider === "shopify" ? (
                  <Link to={`/projects/${id}/shopify`}>
                    <Button variant="secondary">Configura</Button>
                  </Link>
                ) : (
                  <Button variant="secondary" disabled>
                    Connetti (presto)
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </>
  );
}
