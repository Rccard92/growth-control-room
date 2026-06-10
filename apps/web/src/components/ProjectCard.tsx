import { Link } from "react-router-dom";
import type { Project } from "@gcr/shared";
import { StatusBadge } from "./StatusBadge";

interface ProjectCardProps {
  project: Project;
  integrationCount?: number;
}

export function ProjectCard({ project, integrationCount }: ProjectCardProps) {
  return (
    <Link to={`/projects/${project.id}`} className="gcr-project-card">
      <div className="gcr-project-card__header">
        <h3 className="gcr-project-card__name">{project.name}</h3>
        <StatusBadge
          variant={project.status === "active" ? "active" : "not_connected"}
          label={project.status}
        />
      </div>
      <p className="gcr-project-card__desc">
        {project.description ?? project.slug}
      </p>
      <div className="gcr-project-card__footer">
        <span>{integrationCount !== undefined ? `${integrationCount} integrazioni` : "—"}</span>
        <span>Apri →</span>
      </div>
    </Link>
  );
}
