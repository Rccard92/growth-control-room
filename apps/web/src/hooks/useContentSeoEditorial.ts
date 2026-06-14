import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ContentSeoEditorialItemCreate,
  ContentSeoEditorialItemUpdate,
  EditorialPlanGenerateRequest,
} from "@gcr/shared";
import {
  createEditorialItem,
  deleteEditorialItem,
  generateEditorialCalendar,
  getEditorialItems,
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
