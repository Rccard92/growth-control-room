import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ContentSeoEditorialItemCreate,
  ContentSeoEditorialItemUpdate,
  EditorialBriefUpdateRequest,
  EditorialArticleUpdateRequest,
  EditorialItemRescheduleRequest,
  EditorialPlanGenerateRequest,
} from "@gcr/shared";
import {
  createEditorialItem,
  deleteEditorialItem,
  generateEditorialBrief,
  generateEditorialCalendar,
  generateEditorialArticle,
  getEditorialBriefBatchJob,
  getEditorialItemAiUsage,
  getEditorialItems,
  rescheduleEditorialItem,
  startEditorialBriefBatch,
  updateEditorialBrief,
  updateEditorialArticle,
  updateEditorialItem,
} from "../lib/content-api";
import { queryKeys } from "../lib/queryKeys";

export function useEditorialItems(projectId: string | undefined, month?: string) {
  return useQuery({
    queryKey: queryKeys.contentSeo.editorialItems(projectId ?? "", month),
    queryFn: () => getEditorialItems(projectId!, { month }),
    enabled: Boolean(projectId),
  });
}

export function useCreateEditorialItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ContentSeoEditorialItemCreate) =>
      createEditorialItem(projectId, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
    },
  });
}

export function useUpdateEditorialItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: ContentSeoEditorialItemUpdate;
    }) => updateEditorialItem(projectId, itemId, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
    },
  });
}

export function useRescheduleEditorialItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: EditorialItemRescheduleRequest;
    }) => rescheduleEditorialItem(projectId, itemId, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
    },
  });
}

export function useDeleteEditorialItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => deleteEditorialItem(projectId, itemId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
    },
  });
}

export function useGenerateEditorialCalendar(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      data,
      dryRun,
    }: {
      data: EditorialPlanGenerateRequest;
      dryRun?: boolean;
    }) => generateEditorialCalendar(projectId, data, dryRun),
    onSuccess: (_data, variables) => {
      if (!variables.dryRun) {
        void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
      }
    },
  });
}

function invalidateEditorial(qc: ReturnType<typeof useQueryClient>, projectId: string) {
  void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
}

function invalidateEditorialAiUsage(
  qc: ReturnType<typeof useQueryClient>,
  projectId: string,
  itemId: string,
) {
  void qc.invalidateQueries({
    queryKey: ["contentSeo", projectId, "editorialItemAiUsage", itemId],
  });
}

export function useEditorialItemAiUsage(projectId: string, itemId: string | undefined) {
  return useQuery({
    queryKey: ["contentSeo", projectId, "editorialItemAiUsage", itemId ?? ""],
    queryFn: () => getEditorialItemAiUsage(projectId, itemId!),
    enabled: Boolean(projectId && itemId),
  });
}

export function useGenerateEditorialBrief(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => generateEditorialBrief(projectId, itemId),
    onSuccess: (_data, itemId) => {
      invalidateEditorial(qc, projectId);
      invalidateEditorialAiUsage(qc, projectId, itemId);
    },
  });
}

export function useUpdateEditorialBrief(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: EditorialBriefUpdateRequest;
    }) => updateEditorialBrief(projectId, itemId, data),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useStartEditorialBriefBatch(projectId: string) {
  return useMutation({
    mutationFn: (data: { month: string; onlyStatus?: string }) =>
      startEditorialBriefBatch(projectId, data),
  });
}

export function useEditorialBriefBatchJob(
  projectId: string,
  jobId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.contentSeo.editorialBriefJob(projectId, jobId ?? ""),
    queryFn: () => getEditorialBriefBatchJob(projectId, jobId!),
    enabled: enabled && Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "pending" || status === "running") return 2000;
      return false;
    },
  });
}

export function useGenerateEditorialArticle(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => generateEditorialArticle(projectId, itemId),
    onSuccess: (_data, itemId) => {
      invalidateEditorial(qc, projectId);
      invalidateEditorialAiUsage(qc, projectId, itemId);
    },
  });
}

export function useUpdateEditorialArticle(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: EditorialArticleUpdateRequest;
    }) => updateEditorialArticle(projectId, itemId, data),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}
