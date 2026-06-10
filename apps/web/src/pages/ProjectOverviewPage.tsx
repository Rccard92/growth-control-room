import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, PageHeader } from "@gcr/ui";

interface HealthResponse {
  status: string;
  service: string;
  connectors_loaded: boolean;
  connectors_count: number;
}

export function ProjectOverviewPage() {
  const { id } = useParams<{ id: string }>();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error("Health check failed");
        return res.json();
      })
      .then(setHealth)
      .catch(() => setHealthError(true));
  }, []);

  return (
    <>
      <PageHeader
        title={`Progetto ${id}`}
        subtitle="Panoramica del brand e metriche aggregate"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "" },
        ]}
      />
      <div className="placeholder-grid">
        <Card title="Metriche" description="Dashboard KPI — in arrivo">
          <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: 0 }}>
            Collega le integrazioni per visualizzare i dati del progetto.
          </p>
        </Card>
        <Card title="Integrazioni attive" description="0 connesse">
          <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: 0 }}>
            Vai alla sezione Integrazioni per collegare le piattaforme.
          </p>
        </Card>
        <Card title="Stato API" description="Health check backend">
          {health && (
            <div className="health-status">
              API {health.status} — {health.connectors_count} connector registrati
            </div>
          )}
          {healthError && (
            <div className="health-status health-status--error">
              API non raggiungibile. Avvia il backend con <code>pnpm dev:api</code>.
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
