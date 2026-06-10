import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateProjectInput, Integration, Project } from "@gcr/shared";
import { apiFetch } from "../lib/api";
import { queryKeys } from "../lib/queryKeys";

export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects.all,
    queryFn: () => apiFetch<Project[]>("/api/projects"),
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id ?? ""),
    queryFn: () => apiFetch<Project>(`/api/projects/${id}`),
    enabled: Boolean(id),
  });
}

export function useProjectIntegrations(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.integrations(id ?? ""),
    queryFn: () => apiFetch<Integration[]>(`/api/projects/${id}/integrations`),
    enabled: Boolean(id),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateProjectInput) =>
      apiFetch<Project>("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: input.name,
          description: input.description ?? null,
        }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}

export function countConnectedIntegrations(integrations: Integration[]): number {
  return integrations.filter((i) => i.status === "connected").length;
}
