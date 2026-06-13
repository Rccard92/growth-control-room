import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { BrandProfileEnrichRequest } from "@gcr/shared";
import {
  applyBrandProfileProposal,
  enrichBrandProfile,
  getBrandContext,
  getBrandIntelligenceOverview,
  getBrandProfile,
  updateBrandProfile,
} from "../lib/brand-intelligence-api";
import { queryKeys } from "../lib/queryKeys";

function invalidateBrand(projectId: string, qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.overview(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.score(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.context(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.profile(projectId) });
}

export function useBrandIntelligenceOverview(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.overview(projectId ?? ""),
    queryFn: () => getBrandIntelligenceOverview(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useBrandContext(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.context(projectId ?? ""),
    queryFn: () => getBrandContext(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useBrandProfile(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.profile(projectId ?? ""),
    queryFn: () => getBrandProfile(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandProfile(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandProfile>[1]) =>
      updateBrandProfile(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useEnrichBrandProfile(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BrandProfileEnrichRequest) => enrichBrandProfile(projectId, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.profile(projectId) });
    },
  });
}

export function useApplyBrandProfileProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyBrandProfileProposal>[1]) =>
      applyBrandProfileProposal(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}
