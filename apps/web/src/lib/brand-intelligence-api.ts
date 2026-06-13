import type {
  BrandAiGuardrail,
  BrandApplyFactsResponse,
  BrandAsset,
  BrandAudienceInsight,
  BrandClaimRule,
  BrandContentPillar,
  BrandContextBundle,
  BrandExtractBatchResponse,
  BrandExtractedFact,
  BrandExternalSource,
  BrandExternalSourceInput,
  BrandImportBatchListItem,
  BrandImportBatchStartResponse,
  BrandImportBatchStatusResponse,
  BrandIntelligenceOverview,
  BrandKnowledgeScore,
  BrandProductKnowledge,
  BrandProfile,
  BrandSectionDraft,
  BrandSectionDraftApplyResponse,
  BrandSectionDraftListItem,
  BrandSectionDraftSynthesizeResponse,
  BrandSeoStrategy,
  BrandSourceDocument,
  BrandSourceDocumentsUploadResponse,
  BrandVoice,
  FactStatus,
  SectionDraftKey,
  SectionDraftStatus,
  TargetSection,
} from "@gcr/shared";
import { apiFetch, apiUploadForm } from "./api";

export function getBrandIntelligenceOverview(
  projectId: string,
): Promise<BrandIntelligenceOverview> {
  return apiFetch<BrandIntelligenceOverview>(
    `/api/projects/${projectId}/brand-intelligence`,
  );
}

export function getBrandKnowledgeScore(projectId: string): Promise<BrandKnowledgeScore> {
  return apiFetch<BrandKnowledgeScore>(
    `/api/projects/${projectId}/brand-intelligence/score`,
  );
}

export function getBrandContext(projectId: string): Promise<BrandContextBundle> {
  return apiFetch<BrandContextBundle>(
    `/api/projects/${projectId}/brand-intelligence/context`,
  );
}

export function getBrandProfile(projectId: string): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/projects/${projectId}/brand-intelligence/profile`);
}

export function updateBrandProfile(
  projectId: string,
  data: Partial<BrandProfile>,
): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/projects/${projectId}/brand-intelligence/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getBrandVoice(projectId: string): Promise<BrandVoice> {
  return apiFetch<BrandVoice>(`/api/projects/${projectId}/brand-intelligence/voice`);
}

export function updateBrandVoice(
  projectId: string,
  data: Partial<BrandVoice>,
): Promise<BrandVoice> {
  return apiFetch<BrandVoice>(`/api/projects/${projectId}/brand-intelligence/voice`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function listBrandProducts(projectId: string): Promise<BrandProductKnowledge[]> {
  return apiFetch<BrandProductKnowledge[]>(
    `/api/projects/${projectId}/brand-intelligence/products`,
  );
}

export function createBrandProduct(
  projectId: string,
  data: Partial<BrandProductKnowledge>,
): Promise<BrandProductKnowledge> {
  return apiFetch<BrandProductKnowledge>(
    `/api/projects/${projectId}/brand-intelligence/products`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function updateBrandProduct(
  projectId: string,
  itemId: string,
  data: Partial<BrandProductKnowledge>,
): Promise<BrandProductKnowledge> {
  return apiFetch<BrandProductKnowledge>(
    `/api/projects/${projectId}/brand-intelligence/products/${itemId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function deleteBrandProduct(projectId: string, itemId: string): Promise<void> {
  return apiFetch<void>(
    `/api/projects/${projectId}/brand-intelligence/products/${itemId}`,
    { method: "DELETE" },
  );
}

export function listBrandAudience(projectId: string): Promise<BrandAudienceInsight[]> {
  return apiFetch<BrandAudienceInsight[]>(
    `/api/projects/${projectId}/brand-intelligence/audience`,
  );
}

export function createBrandAudience(
  projectId: string,
  data: Partial<BrandAudienceInsight>,
): Promise<BrandAudienceInsight> {
  return apiFetch<BrandAudienceInsight>(
    `/api/projects/${projectId}/brand-intelligence/audience`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function listBrandClaims(projectId: string): Promise<BrandClaimRule[]> {
  return apiFetch<BrandClaimRule[]>(
    `/api/projects/${projectId}/brand-intelligence/claims`,
  );
}

export function createBrandClaim(
  projectId: string,
  data: Partial<BrandClaimRule>,
): Promise<BrandClaimRule> {
  return apiFetch<BrandClaimRule>(`/api/projects/${projectId}/brand-intelligence/claims`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function getBrandSeoStrategy(projectId: string): Promise<BrandSeoStrategy> {
  return apiFetch<BrandSeoStrategy>(
    `/api/projects/${projectId}/brand-intelligence/seo-strategy`,
  );
}

export function updateBrandSeoStrategy(
  projectId: string,
  data: Partial<BrandSeoStrategy>,
): Promise<BrandSeoStrategy> {
  return apiFetch<BrandSeoStrategy>(
    `/api/projects/${projectId}/brand-intelligence/seo-strategy`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function listBrandPillars(projectId: string): Promise<BrandContentPillar[]> {
  return apiFetch<BrandContentPillar[]>(
    `/api/projects/${projectId}/brand-intelligence/content-pillars`,
  );
}

export function createBrandPillar(
  projectId: string,
  data: Partial<BrandContentPillar>,
): Promise<BrandContentPillar> {
  return apiFetch<BrandContentPillar>(
    `/api/projects/${projectId}/brand-intelligence/content-pillars`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function listBrandGuardrails(projectId: string): Promise<BrandAiGuardrail[]> {
  return apiFetch<BrandAiGuardrail[]>(
    `/api/projects/${projectId}/brand-intelligence/guardrails`,
  );
}

export function createBrandGuardrail(
  projectId: string,
  data: Partial<BrandAiGuardrail>,
): Promise<BrandAiGuardrail> {
  return apiFetch<BrandAiGuardrail>(
    `/api/projects/${projectId}/brand-intelligence/guardrails`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function listBrandAssets(projectId: string): Promise<BrandAsset[]> {
  return apiFetch<BrandAsset[]>(`/api/projects/${projectId}/brand-intelligence/assets`);
}

export function createBrandAsset(
  projectId: string,
  data: Partial<BrandAsset>,
): Promise<BrandAsset> {
  return apiFetch<BrandAsset>(`/api/projects/${projectId}/brand-intelligence/assets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function listBrandSourceDocuments(projectId: string): Promise<BrandSourceDocument[]> {
  return apiFetch<BrandSourceDocument[]>(
    `/api/projects/${projectId}/brand-intelligence/sources`,
  );
}

export function uploadBrandSourceDocuments(
  projectId: string,
  files: File[],
  options?: {
    batchName?: string;
    notes?: string;
    brandName?: string;
    websiteUrl?: string;
    sources?: BrandExternalSourceInput[];
    batchId?: string;
  },
): Promise<BrandSourceDocumentsUploadResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  if (options?.batchName) form.append("batchName", options.batchName);
  if (options?.notes) form.append("notes", options.notes);
  if (options?.brandName) form.append("brandName", options.brandName);
  if (options?.websiteUrl) form.append("websiteUrl", options.websiteUrl);
  if (options?.sources?.length) {
    form.append("sources", JSON.stringify(options.sources));
  }
  if (options?.batchId) form.append("batchId", options.batchId);
  return apiUploadForm<BrandSourceDocumentsUploadResponse>(
    `/api/projects/${projectId}/brand-intelligence/sources/upload`,
    form,
  );
}

export function listBatchExternalSources(
  projectId: string,
  batchId: string,
): Promise<BrandExternalSource[]> {
  return apiFetch<BrandExternalSource[]>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/external-sources`,
  );
}

export function addBatchExternalSources(
  projectId: string,
  batchId: string,
  sources: BrandExternalSourceInput[],
): Promise<BrandExternalSource[]> {
  return apiFetch<BrandExternalSource[]>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/external-sources`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sources }),
    },
  );
}

export function fetchBatchExternalSources(
  projectId: string,
  batchId: string,
): Promise<{ fetchedCount: number; warnings: string[] }> {
  return apiFetch<{ fetchedCount: number; warnings: string[] }>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/fetch-sources`,
    { method: "POST" },
  );
}

export function startImportBatch(
  projectId: string,
  batchId: string,
): Promise<BrandImportBatchStartResponse> {
  return apiFetch<BrandImportBatchStartResponse>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/start`,
    { method: "POST" },
  );
}

export function getImportBatchStatus(
  projectId: string,
  batchId: string,
): Promise<BrandImportBatchStatusResponse> {
  return apiFetch<BrandImportBatchStatusResponse>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/status`,
  );
}

export function listImportBatches(projectId: string): Promise<BrandImportBatchListItem[]> {
  return apiFetch<BrandImportBatchListItem[]>(
    `/api/projects/${projectId}/brand-intelligence/import-batches`,
  );
}

export function extractBrandSourceBatch(
  projectId: string,
  documentIds: string[],
): Promise<BrandExtractBatchResponse> {
  return apiFetch<BrandExtractBatchResponse>(
    `/api/projects/${projectId}/brand-intelligence/sources/extract-batch`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ documentIds }),
    },
  );
}

export function listBrandExtractedFacts(
  projectId: string,
  filters?: {
    status?: FactStatus;
    targetSection?: TargetSection;
    sourceDocumentId?: string;
    batchId?: string;
  },
): Promise<BrandExtractedFact[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.targetSection) params.set("targetSection", filters.targetSection);
  if (filters?.sourceDocumentId) params.set("sourceDocumentId", filters.sourceDocumentId);
  if (filters?.batchId) params.set("batchId", filters.batchId);
  const qs = params.toString();
  return apiFetch<BrandExtractedFact[]>(
    `/api/projects/${projectId}/brand-intelligence/extracted-facts${qs ? `?${qs}` : ""}`,
  );
}

export function patchBrandExtractedFact(
  projectId: string,
  factId: string,
  data: Partial<{
    targetSection: TargetSection;
    fieldName: string;
    extractedValue: unknown;
    status: FactStatus;
  }>,
): Promise<BrandExtractedFact> {
  return apiFetch<BrandExtractedFact>(
    `/api/projects/${projectId}/brand-intelligence/extracted-facts/${factId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function applyBrandExtractedFacts(
  projectId: string,
  factIds: string[],
  batchId?: string,
): Promise<BrandApplyFactsResponse> {
  return apiFetch<BrandApplyFactsResponse>(
    `/api/projects/${projectId}/brand-intelligence/extracted-facts/apply`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ factIds, batchId }),
    },
  );
}

export function synthesizeImportBatch(
  projectId: string,
  batchId: string,
): Promise<BrandSectionDraftSynthesizeResponse> {
  return apiFetch<BrandSectionDraftSynthesizeResponse>(
    `/api/projects/${projectId}/brand-intelligence/import-batches/${batchId}/synthesize`,
    { method: "POST" },
  );
}

export function listSectionDrafts(
  projectId: string,
  filters?: { batchId?: string; status?: SectionDraftStatus; sectionKey?: SectionDraftKey },
): Promise<BrandSectionDraftListItem[]> {
  const params = new URLSearchParams();
  if (filters?.batchId) params.set("batchId", filters.batchId);
  if (filters?.status) params.set("status", filters.status);
  if (filters?.sectionKey) params.set("sectionKey", filters.sectionKey);
  const qs = params.toString();
  return apiFetch<BrandSectionDraftListItem[]>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts${qs ? `?${qs}` : ""}`,
  );
}

export function getSectionDraft(projectId: string, draftId: string): Promise<BrandSectionDraft> {
  return apiFetch<BrandSectionDraft>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts/${draftId}`,
  );
}

export function patchSectionDraft(
  projectId: string,
  draftId: string,
  data: Partial<{ draftPayload: unknown; status: SectionDraftStatus; warnings: unknown }>,
): Promise<BrandSectionDraft> {
  return apiFetch<BrandSectionDraft>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts/${draftId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function applySectionDraft(
  projectId: string,
  draftId: string,
): Promise<BrandSectionDraftApplyResponse> {
  return apiFetch<BrandSectionDraftApplyResponse>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts/${draftId}/apply`,
    { method: "POST" },
  );
}

export function applySectionDraftsBatch(
  projectId: string,
  draftIds: string[],
): Promise<BrandSectionDraftApplyResponse> {
  return apiFetch<BrandSectionDraftApplyResponse>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts/apply-batch`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draftIds }),
    },
  );
}

export function regenerateSectionDraft(
  projectId: string,
  draftId: string,
  data?: { instructions?: string; includeFactIds?: string[] },
): Promise<BrandSectionDraft> {
  return apiFetch<BrandSectionDraft>(
    `/api/projects/${projectId}/brand-intelligence/section-drafts/${draftId}/regenerate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data ?? {}),
    },
  );
}
