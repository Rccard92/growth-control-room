import { useQueries } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { Integration } from "@gcr/shared";
import { EmptyState } from "../components/EmptyState";
import { ApiDiagnostics } from "../components/ApiDiagnostics";
import { PageHeader } from "../components/PageHeader";
import { ProjectCard } from "../components/ProjectCard";
import { apiFetch } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";
import { countConnectedIntegrations, useProjects } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

export function ProjectsPage() {
  const { data: projects, isLoading, error } = useProjects();

  const integrationQueries = useQueries({
    queries: (projects ?? []).map((project) => ({
      queryKey: queryKeys.projects.integrations(project.id),
      queryFn: () => apiFetch<Integration[]>(`/api/projects/${project.id}/integrations`),
      staleTime: 60_000,
    })),
  });

  const integrationCounts = new Map<string, number>();
  projects?.forEach((project, index) => {
    const data = integrationQueries[index]?.data;
    if (data) {
      integrationCounts.set(project.id, countConnectedIntegrations(data));
    }
  });

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Project Hub"
        subtitle="Governance multi-brand — ogni progetto è una control room dedicata"
        actions={
          <Link to={APP_ROUTES.newProject} className="gcr-btn gcr-btn--primary">
            Nuovo progetto
          </Link>
        }
      />

      {isLoading && (
        <div className="gcr-grid gcr-grid--auto">
          {[1, 2, 3].map((i) => (
            <div key={i} className="gcr-card" style={{ height: 140 }}>
              <div className="gcr-skeleton" style={{ width: "60%", marginBottom: 12 }} />
              <div className="gcr-skeleton" style={{ width: "90%" }} />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="gcr-alert gcr-alert--error">
          Errore nel caricamento: {error.message}
        </div>
      )}

      {!isLoading && !error && projects?.length === 0 && (
        <EmptyState
          icon="◈"
          title="Nessun progetto ancora"
          description="Crea il tuo primo progetto per iniziare a collegare integrazioni, monitorare KPI e generare insight AI."
          action={
            <Link to={APP_ROUTES.newProject} className="gcr-btn gcr-btn--primary">
              Nuovo progetto
            </Link>
          }
        />
      )}

      {!isLoading && projects && projects.length > 0 && (
        <div className="gcr-grid gcr-grid--auto">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              integrationCount={integrationCounts.get(project.id)}
            />
          ))}
        </div>
      )}

      <ApiDiagnostics />
    </motion.div>
  );
}
