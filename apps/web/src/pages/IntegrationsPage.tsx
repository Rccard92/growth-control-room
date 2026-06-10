import { Link, useParams } from "react-router-dom";
import { INTEGRATIONS } from "@gcr/shared";
import { Button, Card, PageHeader } from "@gcr/ui";

export function IntegrationsPage() {
  const { id } = useParams<{ id: string }>();

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
      <div className="placeholder-grid">
        {INTEGRATIONS.map((integration) => (
          <Card key={integration.type} title={integration.label} description={integration.description}>
            <div className="integration-card">
              <div className="integration-card__header">
                <span className="integration-card__icon">{integration.icon}</span>
                <span className="integration-card__status">Non connessa</span>
              </div>
              {integration.type === "shopify" ? (
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
        ))}
      </div>
    </>
  );
}
