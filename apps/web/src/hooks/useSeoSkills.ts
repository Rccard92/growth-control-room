import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { SeoSkillRunCreateRequest, SeoSkillRunStatus } from "@gcr/shared";
import {
  fetchSeoSkillCatalog,
  fetchSeoSkillRun,
  fetchSeoSkillRunResults,
  listSeoSkillRuns,
  startSeoSkillRun,
} from "../lib/seo-skills-api";
import { queryKeys } from "../lib/queryKeys";

const RUN_POLL_INTERVAL_MS = 2500;

function isRunActive(status?: SeoSkillRunStatus): boolean {
  return status === "pending" || status === "running";
}

export function useSeoSkillCatalog(projectId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.seoSkills.catalog(projectId ?? ""),
    queryFn: () => fetchSeoSkillCatalog(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useSeoSkillRuns(projectId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.seoSkills.runs(projectId ?? ""),
    queryFn: () => listSeoSkillRuns(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useSeoSkillRun(projectId?: string, runId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.seoSkills.run(projectId ?? "", runId ?? ""),
    queryFn: () => fetchSeoSkillRun(projectId!, runId!),
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

export function useSeoSkillRunResults(
  projectId?: string,
  runId?: string,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.seoSkills.runResults(projectId ?? "", runId ?? ""),
    queryFn: () => fetchSeoSkillRunResults(projectId!, runId!),
    enabled: Boolean(projectId) && Boolean(runId) && enabled,
  });
}

export function useStartSeoSkillRun(projectId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: SeoSkillRunCreateRequest) => {
      if (!projectId) {
        throw new Error("projectId is required");
      }
      return startSeoSkillRun(projectId, payload);
    },
    onSuccess: (data) => {
      if (!projectId) return;

      void queryClient.invalidateQueries({
        queryKey: queryKeys.seoSkills.runs(projectId),
      });
      queryClient.setQueryData(queryKeys.seoSkills.run(projectId, data.run.id), {
        run: data.run,
        results: [],
      });
    },
  });
}
