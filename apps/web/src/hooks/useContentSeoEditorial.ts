import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ContentSeoEditorialItemCreate,
  ContentSeoEditorialItemUpdate,
  EditorialBriefUpdateRequest,
  EditorialArticleUpdateRequest,
  EditorialPublishingUpdateRequest,
  EditorialPublishShopifyRequest,
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
  getShopifyBlogs,
  publishEditorialShopify,
  syncEditorialPublishingFromArticle,
  disconnectEditorialShopifyArticle,
  rescheduleEditorialItem,
  startEditorialBriefBatch,
  updateEditorialBrief,
  updateEditorialArticle,
  updateEditorialPublishing,
  updateEditorialItem,
  generateEditorialImage,
  editEditorialImage,
  approveEditorialImage,
  removeEditorialImage,
  syncEditorialImageFromTitle,
  retryEditorialImageUpload,
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

export function useShopifyBlogs(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contentSeo.shopifyBlogs(projectId ?? ""),
    queryFn: () => getShopifyBlogs(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useUpdateEditorialPublishing(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: EditorialPublishingUpdateRequest;
    }) => updateEditorialPublishing(projectId, itemId, data),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function usePublishEditorialShopify(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: EditorialPublishShopifyRequest;
    }) => publishEditorialShopify(projectId, itemId, data),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useSyncEditorialPublishingFromArticle(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => syncEditorialPublishingFromArticle(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useDisconnectEditorialShopifyArticle(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => disconnectEditorialShopifyArticle(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useGenerateEditorialImage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => generateEditorialImage(projectId, itemId),
    onSuccess: (_data, itemId) => {
      invalidateEditorial(qc, projectId);
      invalidateEditorialAiUsage(qc, projectId, itemId);
    },
  });
}

export function useEditEditorialImage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      revisionNote,
    }: {
      itemId: string;
      revisionNote: string;
    }) => editEditorialImage(projectId, itemId, { revisionNote }),
    onSuccess: (_data, variables) => {
      invalidateEditorial(qc, projectId);
      invalidateEditorialAiUsage(qc, projectId, variables.itemId);
    },
  });
}

export function useApproveEditorialImage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => approveEditorialImage(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useRemoveEditorialImage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => removeEditorialImage(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useSyncEditorialImageFromTitle(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => syncEditorialImageFromTitle(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}

export function useRetryEditorialImageUpload(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => retryEditorialImageUpload(projectId, itemId),
    onSuccess: () => invalidateEditorial(qc, projectId),
  });
}
