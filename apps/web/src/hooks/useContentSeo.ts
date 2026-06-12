import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeContentSeo, getContentSeoDashboard, syncContentSeoShopify } from "../lib/content-api";
import { queryKeys } from "../lib/queryKeys";

export function useContentSeoDashboard(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contentSeo.dashboard(projectId ?? ""),
    queryFn: () => getContentSeoDashboard(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useContentSeoSync(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => syncContentSeoShopify(projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.contentSeo.dashboard(projectId),
      });
    },
  });
}

export function useContentSeoAnalyze(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => analyzeContentSeo(projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.contentSeo.dashboard(projectId),
      });
    },
  });
}
