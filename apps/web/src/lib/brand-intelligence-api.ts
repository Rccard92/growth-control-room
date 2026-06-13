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
  BrandIntelligenceOverview,
  BrandKnowledgeScore,
  BrandProductKnowledge,
  BrandProfile,
  BrandSeoStrategy,
  BrandSourceDocument,
  BrandSourceDocumentsUploadResponse,
  BrandVoice,
  FactStatus,
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
): Promise<BrandSourceDocumentsUploadResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  return apiUploadForm<BrandSourceDocumentsUploadResponse>(
    `/api/projects/${projectId}/brand-intelligence/sources/upload`,
    form,
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
  },
): Promise<BrandExtractedFact[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.targetSection) params.set("targetSection", filters.targetSection);
  if (filters?.sourceDocumentId) params.set("sourceDocumentId", filters.sourceDocumentId);
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
): Promise<BrandApplyFactsResponse> {
  return apiFetch<BrandApplyFactsResponse>(
    `/api/projects/${projectId}/brand-intelligence/extracted-facts/apply`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ factIds }),
    },
  );
}
