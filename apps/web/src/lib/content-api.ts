import type {
  SeoAnalyzeCountResponse,
  SeoApplyFieldsResponse,
  SeoApplyResponse,
  SeoCollectionDetailResponse,
  SeoCollectionListResponse,
  SeoContentDebugResponse,
  SeoEntityAnalysis,
  SeoEntitySyncResponse,
  SeoOptimizationProposal,
  SeoOptimizerSyncResponse,
  SeoProductDetailResponse,
  SeoProductListResponse,
  SeoProposalListResponse,
  SeoProposalGenerateFieldResponse,
  SeoMetafieldDefinitionsSyncResponse,
  SeoProposalPreviewResponse,
  ContentSeoDashboard,
  ContentSeoEditorialItem,
  ContentSeoEditorialItemCreate,
  ContentSeoEditorialItemListResponse,
  ContentSeoEditorialItemUpdate,
  EditorialPlanGenerateRequest,
  EditorialPlanGenerateResponse,
  EditorialItemRescheduleRequest,
  EditorialItemRescheduleResponse,
  EditorialBriefUpdateRequest,
  EditorialBriefBatchStartRequest,
  EditorialBriefBatchJobResponse,
  EditorialArticleUpdateRequest,
  EditorialItemAiUsageResponse,
  EditorialPublishingUpdateRequest,
  EditorialPublishShopifyRequest,
  EditorialPublishShopifyResponse,
  ShopifyBlogsListResponse,
} from "@gcr/shared";
import { apiFetch, jsonBody } from "./api";

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

export function getContentSeoDashboard(projectId: string): Promise<ContentSeoDashboard> {
  return apiFetch<ContentSeoDashboard>(`/api/projects/${projectId}/content/seo/dashboard`);
}

export function getProductSeoDetail(
  projectId: string,
  productId: string,
): Promise<SeoProductDetailResponse> {
  return apiFetch<SeoProductDetailResponse>(
    `/api/projects/${projectId}/content/seo/products/${productId}`,
  );
}

export function getCollectionSeoDetail(
  projectId: string,
  collectionId: string,
): Promise<SeoCollectionDetailResponse> {
  return apiFetch<SeoCollectionDetailResponse>(
    `/api/projects/${projectId}/content/seo/collections/${collectionId}`,
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
  options?: { useAi?: boolean; mode?: string },
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/generate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entityType,
        entityId,
        useAi: options?.useAi ?? true,
        mode: options?.mode ?? "fill_missing_and_improve",
      }),
    },
  );
}

export function generateProposalField(
  projectId: string,
  entityType: "product" | "collection",
  entityId: string,
  options: {
    field: string;
    imageId?: string;
    metafieldId?: string | null;
    definitionId?: string;
    namespace?: string;
    key?: string;
    type?: string;
    useAi?: boolean;
  },
): Promise<SeoProposalGenerateFieldResponse> {
  return apiFetch<SeoProposalGenerateFieldResponse>(
    `/api/projects/${projectId}/content/seo/proposals/generate-field`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entityType,
        entityId,
        field: options.field,
        imageId: options.imageId,
        metafieldId: options.metafieldId,
        definitionId: options.definitionId,
        namespace: options.namespace,
        key: options.key,
        type: options.type,
        useAi: options.useAi ?? true,
      }),
    },
  );
}

export function syncMetafieldDefinitions(
  projectId: string,
): Promise<SeoMetafieldDefinitionsSyncResponse> {
  return apiFetch<SeoMetafieldDefinitionsSyncResponse>(
    `/api/projects/${projectId}/content/seo/metafield-definitions/sync`,
    { method: "POST" },
  );
}

export function saveManualProposal(
  projectId: string,
  entityType: "product" | "collection",
  entityId: string,
  proposedValues: Record<string, unknown>,
  changedFields?: string[],
): Promise<SeoOptimizationProposal> {
  return apiFetch<SeoOptimizationProposal>(
    `/api/projects/${projectId}/content/seo/proposals/manual`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entityType, entityId, proposedValues, changedFields }),
    },
  );
}

export function previewProposal(
  projectId: string,
  proposalId: string,
): Promise<SeoProposalPreviewResponse> {
  return apiFetch<SeoProposalPreviewResponse>(
    `/api/projects/${projectId}/content/seo/proposals/${proposalId}/preview`,
    { method: "POST" },
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

export function applyEntityFields(
  projectId: string,
  body: {
    entityType: "product" | "collection";
    entityId: string;
    fields: Record<string, unknown>;
    changedFields: string[];
  },
): Promise<SeoApplyFieldsResponse> {
  return apiFetch<SeoApplyFieldsResponse>(
    `/api/projects/${projectId}/content/seo/entities/apply-fields`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export function syncProductSeo(
  projectId: string,
  productId: string,
): Promise<SeoEntitySyncResponse> {
  return apiFetch<SeoEntitySyncResponse>(
    `/api/projects/${projectId}/content/seo/products/${productId}/sync-shopify`,
    { method: "POST" },
  );
}

export function syncCollectionSeo(
  projectId: string,
  collectionId: string,
): Promise<SeoEntitySyncResponse> {
  return apiFetch<SeoEntitySyncResponse>(
    `/api/projects/${projectId}/content/seo/collections/${collectionId}/sync-shopify`,
    { method: "POST" },
  );
}

export function getContentSeoDebug(projectId: string): Promise<SeoContentDebugResponse> {
  return apiFetch<SeoContentDebugResponse>(
    `/api/projects/${projectId}/content/seo/debug`,
  );
}

export function getEditorialItems(
  projectId: string,
  params?: { month?: string; status?: string; contentType?: string },
): Promise<ContentSeoEditorialItemListResponse> {
  const search = new URLSearchParams();
  if (params?.month) search.set("month", params.month);
  if (params?.status) search.set("status", params.status);
  if (params?.contentType) search.set("contentType", params.contentType);
  const q = search.toString();
  return apiFetch<ContentSeoEditorialItemListResponse>(
    `/api/projects/${projectId}/content/seo/editorial-items${q ? `?${q}` : ""}`,
  );
}

export function createEditorialItem(
  projectId: string,
  data: ContentSeoEditorialItemCreate,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items`,
    { method: "POST", ...jsonBody(data) },
  );
}

export function updateEditorialItem(
  projectId: string,
  itemId: string,
  data: ContentSeoEditorialItemUpdate,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}`,
    { method: "PUT", ...jsonBody(data) },
  );
}

export function rescheduleEditorialItem(
  projectId: string,
  itemId: string,
  data: EditorialItemRescheduleRequest,
): Promise<EditorialItemRescheduleResponse> {
  return apiFetch<EditorialItemRescheduleResponse>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/reschedule`,
    { method: "POST", ...jsonBody(data) },
  );
}

export function deleteEditorialItem(projectId: string, itemId: string): Promise<void> {
  return apiFetch<void>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}`,
    { method: "DELETE" },
  );
}

export function generateEditorialCalendar(
  projectId: string,
  data: EditorialPlanGenerateRequest,
  dryRun = false,
): Promise<EditorialPlanGenerateResponse> {
  const q = dryRun ? "?dryRun=true" : "";
  return apiFetch<EditorialPlanGenerateResponse>(
    `/api/projects/${projectId}/content/seo/editorial-plan/generate-calendar${q}`,
    { method: "POST", ...jsonBody(data) },
  );
}

export function generateEditorialBrief(
  projectId: string,
  itemId: string,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/generate-brief`,
    { method: "POST" },
  );
}

export function updateEditorialBrief(
  projectId: string,
  itemId: string,
  data: EditorialBriefUpdateRequest,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/brief`,
    { method: "PUT", ...jsonBody(data) },
  );
}

export function startEditorialBriefBatch(
  projectId: string,
  data: EditorialBriefBatchStartRequest,
): Promise<EditorialBriefBatchJobResponse> {
  return apiFetch<EditorialBriefBatchJobResponse>(
    `/api/projects/${projectId}/content/seo/editorial-briefs/generate-batch`,
    { method: "POST", ...jsonBody(data) },
  );
}

export function getEditorialBriefBatchJob(
  projectId: string,
  jobId: string,
): Promise<EditorialBriefBatchJobResponse> {
  return apiFetch<EditorialBriefBatchJobResponse>(
    `/api/projects/${projectId}/content/seo/editorial-briefs/jobs/${jobId}`,
  );
}

export function generateEditorialArticle(
  projectId: string,
  itemId: string,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/generate-article`,
    { method: "POST" },
  );
}

export function updateEditorialArticle(
  projectId: string,
  itemId: string,
  data: EditorialArticleUpdateRequest,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/article`,
    { method: "PUT", ...jsonBody(data) },
  );
}

export function getEditorialItemAiUsage(
  projectId: string,
  itemId: string,
): Promise<EditorialItemAiUsageResponse> {
  return apiFetch<EditorialItemAiUsageResponse>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/ai-usage`,
  );
}

export function getShopifyBlogs(projectId: string): Promise<ShopifyBlogsListResponse> {
  return apiFetch<ShopifyBlogsListResponse>(
    `/api/projects/${projectId}/content/seo/shopify/blogs`,
  );
}

export function updateEditorialPublishing(
  projectId: string,
  itemId: string,
  data: EditorialPublishingUpdateRequest,
): Promise<ContentSeoEditorialItem> {
  return apiFetch<ContentSeoEditorialItem>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/publishing`,
    { method: "PUT", ...jsonBody(data) },
  );
}

export function publishEditorialShopify(
  projectId: string,
  itemId: string,
  data: EditorialPublishShopifyRequest,
): Promise<EditorialPublishShopifyResponse> {
  return apiFetch<EditorialPublishShopifyResponse>(
    `/api/projects/${projectId}/content/seo/editorial-items/${itemId}/publish-shopify`,
    { method: "POST", ...jsonBody(data) },
  );
}
