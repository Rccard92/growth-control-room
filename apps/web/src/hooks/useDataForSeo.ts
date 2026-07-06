import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  DataForSeoEstimateRequest,
  DataForSeoTestRequest,
} from "@gcr/shared";
import {
  estimateDataForSeoCost,
  fetchDataForSeoStatus,
  fetchDataForSeoUsage,
  runDataForSeoSandboxTest,
} from "../lib/dataforseo-api";
import { queryKeys } from "../lib/queryKeys";

export function useDataForSeoStatus(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.dataforseo.status(projectId ?? ""),
    queryFn: () => fetchDataForSeoStatus(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useDataForSeoUsage(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.dataforseo.usage(projectId ?? ""),
    queryFn: () => fetchDataForSeoUsage(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useDataForSeoEstimate(projectId: string | undefined) {
  return useMutation({
    mutationFn: (payload: DataForSeoEstimateRequest) =>
      estimateDataForSeoCost(projectId!, payload),
  });
}

export function useDataForSeoSandboxTest(projectId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DataForSeoTestRequest) =>
      runDataForSeoSandboxTest(projectId!, payload),
    onSuccess: () => {
      if (!projectId) return;
      void queryClient.invalidateQueries({ queryKey: queryKeys.dataforseo.status(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.dataforseo.usage(projectId) });
    },
  });
}
