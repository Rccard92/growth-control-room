import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  GrowthAuditFindingsFilters,
  GrowthAuditPageAiAnalysisRequest,
  GrowthAuditPagePerformanceAnalysisRequest,
  GrowthAuditPageRescanRequest,
  GrowthAuditRunCreateRequest,
  GrowthAuditRunStatus,
  GrowthAuditTasksFilters,
} from "@gcr/shared";
import {
  analyzeGrowthAuditPagePerformance,
  analyzeGrowthAuditPageWithAi,
  fetchGrowthAuditEvents,
  fetchGrowthAuditFindings,
  fetchGrowthAuditPageResults,
  fetchGrowthAuditPages,
  fetchGrowthAuditRun,
  fetchGrowthAuditTasks,
  listGrowthAuditRuns,
  rescanGrowthAuditPage,
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

const FINDINGS_TASKS_STATUSES: GrowthAuditRunStatus[] = [
  "analyzing",
  "completed",
  "partial_failed",
];

function canFetchFindingsTasks(status?: GrowthAuditRunStatus): boolean {
  return Boolean(status && FINDINGS_TASKS_STATUSES.includes(status));
}

export function useGrowthAuditFindings(
  projectId?: string,
  runId?: string,
  filters?: GrowthAuditFindingsFilters,
  runStatus?: GrowthAuditRunStatus,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.growthAudit.findings(projectId ?? "", runId ?? "", filters),
    queryFn: () => fetchGrowthAuditFindings(projectId!, runId!, filters),
    enabled:
      Boolean(projectId) &&
      Boolean(runId) &&
      enabled &&
      canFetchFindingsTasks(runStatus),
    select: (data) => data.findings,
  });
}

export function useGrowthAuditTasks(
  projectId?: string,
  runId?: string,
  filters?: GrowthAuditTasksFilters,
  runStatus?: GrowthAuditRunStatus,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.growthAudit.tasks(projectId ?? "", runId ?? "", filters),
    queryFn: () => fetchGrowthAuditTasks(projectId!, runId!, filters),
    enabled:
      Boolean(projectId) &&
      Boolean(runId) &&
      enabled &&
      canFetchFindingsTasks(runStatus),
    select: (data) => data.tasks,
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

export function useRescanGrowthAuditPage(projectId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      runId: string;
      pageId: string;
      payload?: GrowthAuditPageRescanRequest;
    }) => {
      if (!projectId) {
        throw new Error("projectId is required");
      }
      return rescanGrowthAuditPage(
        projectId,
        input.runId,
        input.pageId,
        input.payload,
      );
    },
    onSuccess: (data) => {
      if (!projectId) return;

      const runId = data.run.id;
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.runs(projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.run(projectId, runId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.pages(projectId, runId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.findings(projectId, runId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.tasks(projectId, runId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.events(projectId, runId),
      });
    },
  });
}

export function useGrowthAuditPageResults(
  projectId?: string,
  runId?: string,
  pageId?: string,
  filters?: { resultType?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.growthAudit.pageResults(
      projectId ?? "",
      runId ?? "",
      pageId ?? "",
      filters?.resultType,
    ),
    queryFn: () => fetchGrowthAuditPageResults(projectId!, runId!, pageId!, filters),
    enabled: Boolean(projectId) && Boolean(runId) && Boolean(pageId) && enabled,
    select: (data) => data.results,
  });
}

export function useAnalyzeGrowthAuditPageWithAi(projectId?: string, runId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      pageId: string;
      payload?: GrowthAuditPageAiAnalysisRequest;
    }) => {
      if (!projectId || !runId) {
        throw new Error("projectId and runId are required");
      }
      return analyzeGrowthAuditPageWithAi(projectId, runId, input.pageId, input.payload);
    },
    onSuccess: (data) => {
      if (!projectId) return;

      const resolvedRunId = data.run.id;
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.runs(projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.run(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.pages(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.findings(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.tasks(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.events(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.pageResults(
          projectId,
          resolvedRunId,
          data.page.id,
        ),
      });
    },
  });
}

export function useAnalyzeGrowthAuditPagePerformance(projectId?: string, runId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      pageId: string;
      payload?: GrowthAuditPagePerformanceAnalysisRequest;
    }) => {
      if (!projectId || !runId) {
        throw new Error("projectId and runId are required");
      }
      return analyzeGrowthAuditPagePerformance(projectId, runId, input.pageId, input.payload);
    },
    onSuccess: (data) => {
      if (!projectId) return;

      const resolvedRunId = data.run.id;
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.runs(projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.run(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.pages(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.findings(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.tasks(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.events(projectId, resolvedRunId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.growthAudit.pageResults(
          projectId,
          resolvedRunId,
          data.page.id,
        ),
      });
    },
  });
}
