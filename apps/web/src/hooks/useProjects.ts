import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateProjectInput, Integration, Project, UpdateProjectInput } from "@gcr/shared";
import { apiFetch } from "../lib/api";
import { createProject, updateProject } from "../lib/projects-api";
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
    mutationFn: (input: CreateProjectInput) => createProject(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}

export function useUpdateProject(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateProjectInput) => {
      if (!projectId) {
        throw new Error("Project id is required");
      }
      return updateProject(projectId, input);
    },
    onSuccess: (project) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(project.id) });
    },
  });
}

export function countConnectedIntegrations(integrations: Integration[]): number {
  return integrations.filter((i) => i.status === "connected").length;
}
