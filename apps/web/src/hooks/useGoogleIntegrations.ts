import { useMutation, useQuery } from "@tanstack/react-query";
import type { GoogleOAuthStartRequest } from "@gcr/shared";
import {
  fetchGoogleIntegrationStatus,
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
