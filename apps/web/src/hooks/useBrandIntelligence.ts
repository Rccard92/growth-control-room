import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { BrandProfileEnrichRequest, VisualExtractRequest } from "@gcr/shared";
import {
  applyBrandIdentityProposal,
  applyBrandProfileProposal,
  applyBrandSafeClaimsProposal,
  applyVisualProposal,
  enrichBrandProfile,
  extractVisualFromWebsite,
  getBrandContext,
  getBrandIdentity,
  getBrandIntelligenceOverview,
  getBrandProfile,
  getBrandSafeClaims,
  getBrandVisualIdentity,
  importBrandIdentityFromFile,
  importBrandSafeClaimsFromFile,
  updateBrandIdentity,
  updateBrandProfile,
  updateBrandSafeClaims,
  updateBrandVisualIdentity,
} from "../lib/brand-intelligence-api";
import { queryKeys } from "../lib/queryKeys";

function invalidateBrand(projectId: string, qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.overview(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.score(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.context(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.profile(projectId) });
  void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.identity(projectId) });
  void qc.invalidateQueries({
    queryKey: queryKeys.brandIntelligence.visualIdentity(projectId),
  });
  void qc.invalidateQueries({
    queryKey: queryKeys.brandIntelligence.safeClaims(projectId),
  });
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

export function useBrandIdentity(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.identity(projectId ?? ""),
    queryFn: () => getBrandIdentity(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandIdentity(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandIdentity>[1]) =>
      updateBrandIdentity(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useImportBrandIdentityFromFile(projectId: string) {
  return useMutation({
    mutationFn: (file: File) => importBrandIdentityFromFile(projectId, file),
  });
}

export function useApplyBrandIdentityProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyBrandIdentityProposal>[1]) =>
      applyBrandIdentityProposal(projectId, data),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.brandIntelligence.identity(projectId), data.brandIdentity);
      invalidateBrand(projectId, qc);
    },
  });
}

export function useBrandVisualIdentity(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.visualIdentity(projectId ?? ""),
    queryFn: () => getBrandVisualIdentity(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandVisualIdentity(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandVisualIdentity>[1]) =>
      updateBrandVisualIdentity(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useExtractVisualFromWebsite(projectId: string) {
  return useMutation({
    mutationFn: (data: VisualExtractRequest) => extractVisualFromWebsite(projectId, data),
  });
}

export function useApplyVisualProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyVisualProposal>[1]) =>
      applyVisualProposal(projectId, data),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.brandIntelligence.visualIdentity(projectId), data.visualIdentity);
      invalidateBrand(projectId, qc);
    },
  });
}

export function useBrandSafeClaims(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.safeClaims(projectId ?? ""),
    queryFn: () => getBrandSafeClaims(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateBrandSafeClaims(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateBrandSafeClaims>[1]) =>
      updateBrandSafeClaims(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useImportBrandSafeClaimsFromFile(projectId: string) {
  return useMutation({
    mutationFn: (file: File) => importBrandSafeClaimsFromFile(projectId, file),
  });
}

export function useApplyBrandSafeClaimsProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyBrandSafeClaimsProposal>[1]) =>
      applyBrandSafeClaimsProposal(projectId, data),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.brandIntelligence.safeClaims(projectId), data.safeClaims);
      invalidateBrand(projectId, qc);
    },
  });
}
