import type {
  SeoAnalyzeCountResponse,
  SeoApplyResponse,
  SeoCollectionListResponse,
  SeoEntityAnalysis,
  SeoOptimizationProposal,
  SeoOptimizerSyncResponse,
  SeoProductListResponse,
  SeoProposalListResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

export function syncSeoOptimizer(projectId: string): Promise<SeoOptimizerSyncResponse> {
  return apiFetch<SeoOptimizerSyncResponse>(
    `/api/projects/${projectId}/content/seo/sync-shopify`,
    { method: "POST" },
  );
}

export function analyzeProductsSeo(projectId: string): Promise<SeoAnalyzeCountResponse> {
  return apiFetch<SeoAnalyzeCountResponse>(
    `/api/projects/${projectId}/content/seo/products/analyze`,
    { method: "POST" },
  );
}

export function analyzeCollectionsSeo(projectId: string): Promise<SeoAnalyzeCountResponse> {
  return apiFetch<SeoAnalyzeCountResponse>(
    `/api/projects/${projectId}/content/seo/collections/analyze`,
    { method: "POST" },
  );
}

export function getProductsSeo(projectId: string): Promise<SeoProductListResponse> {
  return apiFetch<SeoProductListResponse>(`/api/projects/${projectId}/content/seo/products`);
}

export function getCollectionsSeo(projectId: string): Promise<SeoCollectionListResponse> {
  return apiFetch<SeoCollectionListResponse>(
    `/api/projects/${projectId}/content/seo/collections`,
  );
}

export function getProductAnalysis(
  projectId: string,
  entityId: string,
): Promise<SeoEntityAnalysis> {
  return apiFetch<SeoEntityAnalysis>(
    `/api/projects/${projectId}/content/seo/products/${entityId}/analysis`,
  );
}

export function getCollectionAnalysis(
  projectId: string,
  entityId: string,
): Promise<SeoEntityAnalysis> {
  return apiFetch<SeoEntityAnalysis>(
    `/api/projects/${projectId}/content/seo/collections/${entityId}/analysis`,
  );
}

export function listProposals(
  projectId: string,
  status?: string,
): Promise<SeoProposalListResponse> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<SeoProposalListResponse>(
    `/api/projects/${projectId}/content/seo/proposals${params}`,
  );
}

export function generateProposal(
  projectId: string,
  entityType: "product" | "collection",
  entityId: string,
  useAi = true,
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/generate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entityType, entityId, useAi }),
    },
  );
}

export function getProposal(
  projectId: string,
  proposalId: string,
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/${proposalId}`,
  );
}

export function approveProposal(
  projectId: string,
  proposalId: string,
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/${proposalId}/approve`,
    { method: "POST" },
  );
}

export function rejectProposal(
  projectId: string,
  proposalId: string,
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/${proposalId}/reject`,
    { method: "POST" },
  );
}

export function applyProposal(
  projectId: string,
  proposalId: string,
): Promise<SeoApplyResponse> {
  return apiFetch<SeoApplyResponse>(
    `/api/projects/${projectId}/content/seo/proposals/${proposalId}/apply`,
    { method: "POST" },
  );
}
