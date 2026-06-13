import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  applyBrandExtractedFacts,
  createBrandAsset,
  createBrandAudience,
  createBrandClaim,
  createBrandGuardrail,
  createBrandPillar,
  createBrandProduct,
  extractBrandSourceBatch,
  getBrandContext,
  getBrandIntelligenceOverview,
  getBrandKnowledgeScore,
  getBrandProfile,
  getBrandSeoStrategy,
  getBrandVoice,
  getImportBatchStatus,
  listBrandAssets,
  listBrandAudience,
  listBrandClaims,
  listBrandExtractedFacts,
  listBrandGuardrails,
  listBrandPillars,
  listBrandProducts,
  listBrandSourceDocuments,
  listImportBatches,
  listSectionDrafts,
  patchBrandExtractedFact,
  patchSectionDraft,
  applySectionDraft,
  regenerateSectionDraft,
  getSectionDraft,
  synthesizeImportBatch,
  startImportBatch,
  updateBrandProfile,
  updateBrandSeoStrategy,
  updateBrandVoice,
  uploadBrandSourceDocuments,
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

export function useBrandSourceDocuments(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.sources(projectId ?? ""),
    queryFn: () => listBrandSourceDocuments(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useUploadBrandSources(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      files,
      batchName,
      notes,
      brandName,
      websiteUrl,
      sources,
      batchId,
    }: {
      files: File[];
      batchName?: string;
      notes?: string;
      brandName?: string;
      websiteUrl?: string;
      sources?: import("@gcr/shared").BrandExternalSourceInput[];
      batchId?: string;
    }) =>
      uploadBrandSourceDocuments(projectId, files, {
        batchName,
        notes,
        brandName,
        websiteUrl,
        sources,
        batchId,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.sources(projectId) });
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.importBatches(projectId) });
    },
  });
}

const POLLING_STATUSES = new Set(["pending", "uploading", "extracting", "ai_processing"]);

export function useImportBatchStatus(
  projectId: string | undefined,
  batchId: string | undefined,
  options?: { enabled?: boolean; polling?: boolean },
) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.importBatch(projectId ?? "", batchId ?? ""),
    queryFn: () => getImportBatchStatus(projectId!, batchId!),
    enabled: Boolean(projectId && batchId && (options?.enabled ?? true)),
    refetchInterval: (query) => {
      if (!options?.polling) return false;
      const status = query.state.data?.status;
      if (!status) return 2000;
      return POLLING_STATUSES.has(status) ? 2000 : false;
    },
  });
}

export function useImportBatches(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.importBatches(projectId ?? ""),
    queryFn: () => listImportBatches(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useStartImportBatch(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (batchId: string) => startImportBatch(projectId, batchId),
    onSuccess: (_data, batchId) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.brandIntelligence.importBatch(projectId, batchId),
      });
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.importBatches(projectId) });
    },
  });
}

export function useExtractBrandSourcesBatch(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (documentIds: string[]) => extractBrandSourceBatch(projectId, documentIds),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.sources(projectId) });
      void qc.invalidateQueries({
        queryKey: ["brandIntelligence", projectId, "extractedFacts"],
      });
    },
  });
}

export function useBrandExtractedFacts(
  projectId: string | undefined,
  filters?: Parameters<typeof listBrandExtractedFacts>[1],
) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.extractedFacts(
      projectId ?? "",
      filters as Record<string, string | undefined>,
    ),
    queryFn: () => listBrandExtractedFacts(projectId!, filters),
    enabled: Boolean(projectId),
  });
}

export function usePatchBrandExtractedFact(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      factId,
      data,
    }: {
      factId: string;
      data: Parameters<typeof patchBrandExtractedFact>[2];
    }) => patchBrandExtractedFact(projectId, factId, data),
    onSuccess: () => {
      void qc.invalidateQueries({
        queryKey: ["brandIntelligence", projectId, "extractedFacts"],
      });
    },
  });
}

export function useApplyBrandExtractedFacts(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ factIds, batchId }: { factIds: string[]; batchId?: string }) =>
      applyBrandExtractedFacts(projectId, factIds, batchId),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({
        queryKey: ["brandIntelligence", projectId, "extractedFacts"],
      });
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.sources(projectId) });
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.importBatches(projectId) });
    },
  });
}

export function useSectionDrafts(
  projectId: string | undefined,
  filters?: Parameters<typeof listSectionDrafts>[1],
) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.sectionDrafts(
      projectId ?? "",
      filters as Record<string, string | undefined>,
    ),
    queryFn: () => listSectionDrafts(projectId!, filters),
    enabled: Boolean(projectId),
  });
}

export function useSectionDraft(projectId: string | undefined, draftId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.brandIntelligence.sectionDraft(projectId ?? "", draftId ?? ""),
    queryFn: () => getSectionDraft(projectId!, draftId!),
    enabled: Boolean(projectId && draftId),
  });
}

export function usePatchSectionDraft(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      draftId,
      data,
    }: {
      draftId: string;
      data: Parameters<typeof patchSectionDraft>[2];
    }) => patchSectionDraft(projectId, draftId, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDrafts"] });
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDraft"] });
    },
  });
}

export function useApplySectionDraft(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (draftId: string) => applySectionDraft(projectId, draftId),
    onSuccess: () => {
      invalidateBrand(projectId, qc);
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDrafts"] });
    },
  });
}

export function useRegenerateSectionDraft(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      draftId,
      instructions,
    }: {
      draftId: string;
      instructions?: string;
    }) => regenerateSectionDraft(projectId, draftId, { instructions }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDrafts"] });
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDraft"] });
    },
  });
}

export function useSynthesizeImportBatch(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (batchId: string) => synthesizeImportBatch(projectId, batchId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["brandIntelligence", projectId, "sectionDrafts"] });
      void qc.invalidateQueries({ queryKey: queryKeys.brandIntelligence.importBatches(projectId) });
    },
  });
}
