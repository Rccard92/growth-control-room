import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createBrandAsset,
  createBrandAudience,
  createBrandClaim,
  createBrandGuardrail,
  createBrandPillar,
  createBrandProduct,
  getBrandContext,
  getBrandIntelligenceOverview,
  getBrandKnowledgeScore,
  getBrandProfile,
  getBrandSeoStrategy,
  getBrandVoice,
  listBrandAssets,
  listBrandAudience,
  listBrandClaims,
  listBrandGuardrails,
  listBrandPillars,
  listBrandProducts,
  updateBrandProfile,
  updateBrandSeoStrategy,
  updateBrandVoice,
} from "../lib/brand-intelligence-api";
import { queryKeys } from "../lib/queryKeys";

function invalidateBrand(projectId: string, qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.overview(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.score(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.context(projectId) });
}

export function useBrandIntelligenceOverview(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.overview(projectId ?? ""),
    queryFn: () => getBrandIntelligenceOverview(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useBrandKnowledgeScore(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.score(projectId ?? ""),
    queryFn: () => getBrandKnowledgeScore(projectId!),
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
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.profile(projectId) });
    },
  });
}

export function useBrandVoice(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.voice(projectId ?? ""),
    queryFn: () => getBrandVoice(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandVoice(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandVoice>[1]) =>
      updateBrandVoice(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.voice(projectId) });
    },
  });
}

export function useBrandProducts(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.products(projectId ?? ""),
    queryFn: () => listBrandProducts(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandProduct(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandProduct>[1]) =>
      createBrandProduct(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.products(projectId) });
    },
  });
}

export function useBrandAudience(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.audience(projectId ?? ""),
    queryFn: () => listBrandAudience(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandAudience(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandAudience>[1]) =>
      createBrandAudience(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.audience(projectId) });
    },
  });
}

export function useBrandClaims(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.claims(projectId ?? ""),
    queryFn: () => listBrandClaims(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandClaim(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandClaim>[1]) =>
      createBrandClaim(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.claims(projectId) });
    },
  });
}

export function useBrandSeoStrategy(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.seoStrategy(projectId ?? ""),
    queryFn: () => getBrandSeoStrategy(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandSeoStrategy(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandSeoStrategy>[1]) =>
      updateBrandSeoStrategy(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({
        queryKey: queryKeys.brandIntelligence.seoStrategy(projectId),
      });
    },
  });
}

export function useBrandPillars(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.pillars(projectId ?? ""),
    queryFn: () => listBrandPillars(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandPillar(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandPillar>[1]) =>
      createBrandPillar(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.pillars(projectId) });
    },
  });
}

export function useBrandGuardrails(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.guardrails(projectId ?? ""),
    queryFn: () => listBrandGuardrails(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandGuardrail(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandGuardrail>[1]) =>
      createBrandGuardrail(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.guardrails(projectId) });
    },
  });
}

export function useBrandAssets(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.assets(projectId ?? ""),
    queryFn: () => listBrandAssets(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useCreateBrandAsset(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createBrandAsset>[1]) =>
      createBrandAsset(projectId, data),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.assets(projectId) });
    },
  });
}
