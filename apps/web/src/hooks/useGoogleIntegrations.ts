import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { GoogleOAuthStartRequest, SelectSearchConsoleSiteRequest } from "@gcr/shared";
import {
  fetchGoogleIntegrationStatus,
  fetchSearchConsoleSites,
  selectSearchConsoleSite,
  startGoogleOAuth,
} from "../lib/google-integrations-api";
import { queryKeys } from "../lib/queryKeys";

export function useGoogleIntegrationStatus(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.google.status(projectId ?? ""),
    queryFn: () => fetchGoogleIntegrationStatus(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useSearchConsoleSites(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.google.searchConsoleSites(projectId ?? ""),
    queryFn: () => fetchSearchConsoleSites(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useSelectSearchConsoleSite(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SelectSearchConsoleSiteRequest) => {
      if (!projectId) {
        throw new Error("Project id is required");
      }
      return selectSearchConsoleSite(projectId, payload);
    },
    onSuccess: () => {
      if (!projectId) return;
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.detail(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.google.status(projectId) });
    },
  });
}

export function useStartGoogleOAuth(projectId: string | undefined) {
  return useMutation({
    mutationFn: (payload?: GoogleOAuthStartRequest) => {
      if (!projectId) {
        throw new Error("Project id is required");
      }
      return startGoogleOAuth(projectId, payload);
    },
  });
}
