import { useQuery } from "@tanstack/react-query";
import type { AiUsageFilters } from "@gcr/shared";
import {
  getAiBudgetStatus,
  getAiUsageEstimate,
  getAiUsageLog,
  getAiUsageLogs,
  getAiUsageSummary,
} from "../lib/ai-usage-api";
import { queryKeys } from "../lib/queryKeys";

export function useAiUsageSummary(projectId: string, filters?: AiUsageFilters) {
  return useQuery({
    queryKey: queryKeys.aiUsage.summary(projectId, filters),
    queryFn: () => getAiUsageSummary(projectId, filters),
    enabled: Boolean(projectId),
  });
}

export function useAiUsageLogs(projectId: string, filters?: AiUsageFilters) {
  return useQuery({
    queryKey: queryKeys.aiUsage.logs(projectId, filters),
    queryFn: () => getAiUsageLogs(projectId, filters),
    enabled: Boolean(projectId),
  });
}

export function useAiUsageLog(projectId: string, logId: string | null) {
  return useQuery({
    queryKey: queryKeys.aiUsage.logDetail(projectId, logId ?? ""),
    queryFn: () => getAiUsageLog(projectId, logId!),
    enabled: Boolean(projectId && logId),
  });
}

export function useAiBudgetStatus(projectId: string) {
  return useQuery({
    queryKey: queryKeys.aiUsage.budget(projectId),
    queryFn: () => getAiBudgetStatus(projectId),
    enabled: Boolean(projectId),
    staleTime: 60_000,
  });
}

export function useAiUsageEstimate(
  projectId: string,
  operation: string,
  count: number,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.aiUsage.estimate(projectId, operation, count),
    queryFn: () => getAiUsageEstimate(projectId, operation, count),
    enabled: Boolean(projectId) && enabled && count > 0,
  });
}
