import type { CreateProjectInput, Project, UpdateProjectInput } from "@gcr/shared";
import { apiFetch } from "./api";

export function createProject(input: CreateProjectInput): Promise<Project> {
  return apiFetch<Project>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      description: input.description ?? null,
      publicSiteUrl: input.publicSiteUrl ?? null,
    }),
  });
}

export function updateProject(projectId: string, payload: UpdateProjectInput): Promise<Project> {
  return apiFetch<Project>(`/api/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
