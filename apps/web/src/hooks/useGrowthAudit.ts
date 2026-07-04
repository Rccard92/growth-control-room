import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { GrowthAuditRunCreateRequest, GrowthAuditRunStatus } from "@gcr/shared";
import {
  fetchGrowthAuditEvents,
  fetchGrowthAuditPages,
  fetchGrowthAuditRun,
  listGrowthAuditRuns,
  startGrowthAuditRun,
} from "../lib/growth-audit-api";
import { queryKeys } from "../lib/queryKeys";

const RUN_POLL_INTERVAL_MS = 2000;

const ACTIVE_RUN_STATUSES: GrowthAuditRunStatus[] = [
  "pending",
  "queued",
  "discovering",
  "classifying",
  "analyzing",
  "ready_for_analysis",
];

function isRunActive(status?: GrowthAuditRunStatus): boolean {
  return Boolean(status && ACTIVE_RUN_STATUSES.includes(status));
}

export function useGrowthAuditRuns(projectId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.growthAudit.runs(projectId ?? ""),
    queryFn: () => listGrowthAuditRuns(projectId!),
    enabled: Boolean(projectId) && enabled,
    select: (data) => data.runs,
  });
}

export function useGrowthAuditRun(projectId?: string, runId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.growthAudit.run(projectId ?? "", runId ?? ""),
    queryFn: () => fetchGrowthAuditRun(projectId!, runId!),
    enabled: Boolean(projectId) && Boolean(runId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      if (status && isRunActive(status)) {
        return RUN_POLL_INTERVAL_MS;
      }
      return false;
    },
  });
}

export function useGrowthAuditPages(projectId?: string, runId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.growthAudit.pages(projectId ?? "", runId ?? ""),
    queryFn: () => fetchGrowthAuditPages(projectId!, runId!),
    enabled: Boolean(projectId) && Boolean(runId) && enabled,
    select: (data) => data.pages,
  });
}

export function useGrowthAuditEvents(projectId?: string, runId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.growthAudit.events(projectId ?? "", runId ?? ""),
    queryFn: () => fetchGrowthAuditEvents(projectId!, runId!),
    enabled: Boolean(projectId) && Boolean(runId) && enabled,
    select: (data) => data.events,
  });
}

export function useStartGrowthAuditRun(projectId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: GrowthAuditRunCreateRequest) => {
      if (!projectId) {
        throw new Error("projectId is required");
      }
      return startGrowthAuditRun(projectId, payload);
    },
    onSuccess: (data) => {
      if (!projectId) return;

      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.runs(projectId),
      });
      queryClient.setQueryData(queryKeys.growthAudit.run(projectId, data.run.id), {
        run: data.run,
        pages: [],
        events: [],
        findingsCount: 0,
        tasksCount: 0,
      });
    },
  });
}
