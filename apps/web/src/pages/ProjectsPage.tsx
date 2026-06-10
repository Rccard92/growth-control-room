import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Project } from "@gcr/shared";
import { Button, Card, PageHeader } from "@gcr/ui";
import { apiFetch } from "../lib/api";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Project[]>("/api/projects")
      .then(setProjects)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <PageHeader
        title="Progetti"
        subtitle="Gestisci i tuoi brand e-commerce e marketing"
        actions={
          <Link to="/projects/new">
            <Button>Nuovo progetto</Button>
          </Link>
        }
      />
      {loading && (
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>Caricamento progetti…</p>
      )}
      {error && (
        <p style={{ color: "#dc2626", fontSize: "0.875rem" }}>
          Errore nel caricamento: {error}
        </p>
      )}
      {!loading && !error && projects.length === 0 && (
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>
          Nessun progetto. Crea il primo con il pulsante in alto.
        </p>
      )}
      <div className="placeholder-grid">
        {projects.map((project) => (
          <Card
            key={project.id}
            title={project.name}
            description={project.description ?? project.slug}
          >
            <Link to={`/projects/${project.id}`}>
              <Button variant="secondary">Apri progetto</Button>
            </Link>
          </Card>
        ))}
      </div>
    </>
  );
}
