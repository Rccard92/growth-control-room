import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { BrandProfileEnrichRequest, VisualExtractRequest } from "@gcr/shared";
import {
  applyBrandIdentityProposal,
  applyBrandProfileProposal,
  applyBrandSafeClaimsProposal,
  applyProductKnowledgeGeneralProposal,
  applyProductKnowledgeItemsImportProposal,
  applyVisualProposal,
  createProductKnowledgeItemFromShopify,
  deleteProductKnowledgeItem,
  enrichBrandProfile,
  extractVisualFromWebsite,
  getBrandContext,
  getBrandIdentity,
  getBrandIntelligenceOverview,
  getBrandProfile,
  getBrandSafeClaims,
  getBrandVisualIdentity,
  getProductKnowledgeGeneral,
  getProductKnowledgeItems,
  getProductKnowledgeShopifyProducts,
  importBrandIdentityFromFile,
  importBrandSafeClaimsFromFile,
  importProductKnowledgeGeneralFromFile,
  importProductKnowledgeItemsFromFile,
  updateBrandIdentity,
  updateBrandProfile,
  updateBrandSafeClaims,
  updateBrandVisualIdentity,
  updateProductKnowledgeGeneral,
  updateProductKnowledgeItem,
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
  void qc.invalidateQueries({
    queryKey: queryKeys.brandIntelligence.productKnowledgeGeneral(projectId),
  });
  void qc.invalidateQueries({
    queryKey: queryKeys.brandIntelligence.productKnowledgeItems(projectId),
  });
  void qc.invalidateQueries({
    queryKey: queryKeys.brandIntelligence.productKnowledgeShopifyProducts(projectId),
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

export function useProductKnowledgeGeneral(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.productKnowledgeGeneral(projectId ?? ""),
    queryFn: () => getProductKnowledgeGeneral(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUpdateProductKnowledgeGeneral(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof updateProductKnowledgeGeneral>[1]) =>
      updateProductKnowledgeGeneral(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useImportProductKnowledgeGeneralFromFile(projectId: string) {
  return useMutation({
    mutationFn: (file: File) => importProductKnowledgeGeneralFromFile(projectId, file),
  });
}

export function useApplyProductKnowledgeGeneralProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyProductKnowledgeGeneralProposal>[1]) =>
      applyProductKnowledgeGeneralProposal(projectId, data),
    onSuccess: (data) => {
      qc.setQueryData(
        queryKeys.brandIntelligence.productKnowledgeGeneral(projectId),
        data.general,
      );
      invalidateBrand(projectId, qc);
    },
  });
}

export function useProductKnowledgeItems(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.productKnowledgeItems(projectId ?? ""),
    queryFn: () => getProductKnowledgeItems(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useProductKnowledgeShopifyProducts(
  projectId: string | undefined,
  enabled = false,
) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.productKnowledgeShopifyProducts(projectId ?? ""),
    queryFn: () => getProductKnowledgeShopifyProducts(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useCreateProductKnowledgeItemFromShopify(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof createProductKnowledgeItemFromShopify>[1]) =>
      createProductKnowledgeItemFromShopify(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useImportProductKnowledgeItemsFromFile(projectId: string) {
  return useMutation({
    mutationFn: (file: File) => importProductKnowledgeItemsFromFile(projectId, file),
  });
}

export function useApplyProductKnowledgeItemsImportProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof applyProductKnowledgeItemsImportProposal>[1]) =>
      applyProductKnowledgeItemsImportProposal(projectId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useUpdateProductKnowledgeItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string;
      data: Parameters<typeof updateProductKnowledgeItem>[2];
    }) => updateProductKnowledgeItem(projectId, itemId, data),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}

export function useDeleteProductKnowledgeItem(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => deleteProductKnowledgeItem(projectId, itemId),
    onSuccess: () => invalidateBrand(projectId, qc),
  });
}
