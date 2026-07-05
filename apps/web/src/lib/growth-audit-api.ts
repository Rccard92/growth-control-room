import type {
  GrowthAuditEventsListResponse,
  GrowthAuditFindingsFilters,
  GrowthAuditFindingsListResponse,
  GrowthAuditPageAiAnalysisRequest,
  GrowthAuditPageAiAnalysisResponse,
  GrowthAuditPagePerformanceAnalysisRequest,
  GrowthAuditPagePerformanceAnalysisResponse,
  GrowthAuditPageRescanRequest,
  GrowthAuditPageRescanResponse,
  GrowthAuditPageResultsListResponse,
  GrowthAuditSearchConsoleAnalysisRequest,
  GrowthAuditSearchConsoleAnalysisResponse,
  GrowthAuditAnalyticsAnalysisRequest,
  GrowthAuditAnalyticsAnalysisResponse,
  GrowthAuditShopifyCommerceAnalysisRequest,
  GrowthAuditShopifyCommerceAnalysisResponse,
  GrowthAuditGa4EcommerceAnalysisRequest,
  GrowthAuditGa4EcommerceAnalysisResponse,
  GrowthAuditMerchantCenterAnalysisRequest,
  GrowthAuditMerchantCenterAnalysisResponse,
  GrowthAuditPagesListResponse,
  GrowthAuditRunCreateRequest,
  GrowthAuditRunDetailResponse,
  GrowthAuditRunsListResponse,
  GrowthAuditStartResponse,
  GrowthAuditTasksFilters,
  GrowthAuditTasksListResponse,
} from "@gcr/shared";
import { apiFetch, jsonBody } from "./api";

function growthAuditBasePath(projectId: string): string {
  return `/api/projects/${projectId}/growth-audit`;
}

export function startGrowthAuditRun(
  projectId: string,
  payload: GrowthAuditRunCreateRequest,
): Promise<GrowthAuditStartResponse> {
  return apiFetch<GrowthAuditStartResponse>(`${growthAuditBasePath(projectId)}/runs`, {
    method: "POST",
    ...jsonBody(payload),
  });
}

export function listGrowthAuditRuns(
  projectId: string,
  limit = 20,
): Promise<GrowthAuditRunsListResponse> {
  const params = new URLSearchParams();
  if (limit !== 20) {
    params.set("limit", String(limit));
  }
  const query = params.toString();
  const path = `${growthAuditBasePath(projectId)}/runs${query ? `?${query}` : ""}`;
  return apiFetch<GrowthAuditRunsListResponse>(path);
}

export function fetchGrowthAuditRun(
  projectId: string,
  runId: string,
): Promise<GrowthAuditRunDetailResponse> {
  return apiFetch<GrowthAuditRunDetailResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}`,
  );
}

export function fetchGrowthAuditPages(
  projectId: string,
  runId: string,
): Promise<GrowthAuditPagesListResponse> {
  return apiFetch<GrowthAuditPagesListResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/pages`,
  );
}

export function fetchGrowthAuditEvents(
  projectId: string,
  runId: string,
): Promise<GrowthAuditEventsListResponse> {
  return apiFetch<GrowthAuditEventsListResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/events`,
  );
}

function buildFilterQuery(filters?: GrowthAuditFindingsFilters | GrowthAuditTasksFilters): string {
  if (!filters) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function fetchGrowthAuditFindings(
  projectId: string,
  runId: string,
  filters?: GrowthAuditFindingsFilters,
): Promise<GrowthAuditFindingsListResponse> {
  const query = buildFilterQuery(filters);
  return apiFetch<GrowthAuditFindingsListResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/findings${query}`,
  );
}

export function fetchGrowthAuditTasks(
  projectId: string,
  runId: string,
  filters?: GrowthAuditTasksFilters,
): Promise<GrowthAuditTasksListResponse> {
  const query = buildFilterQuery(filters);
  return apiFetch<GrowthAuditTasksListResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/tasks${query}`,
  );
}

export function rescanGrowthAuditPage(
  projectId: string,
  runId: string,
  pageId: string,
  payload?: GrowthAuditPageRescanRequest,
): Promise<GrowthAuditPageRescanResponse> {
  return apiFetch<GrowthAuditPageRescanResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/pages/${pageId}/rescan`,
    {
      method: "POST",
      ...jsonBody(payload ?? { clearPreviousOpenItems: true }),
    },
  );
}

export function analyzeGrowthAuditPageWithAi(
  projectId: string,
  runId: string,
  pageId: string,
  payload?: GrowthAuditPageAiAnalysisRequest,
): Promise<GrowthAuditPageAiAnalysisResponse> {
  return apiFetch<GrowthAuditPageAiAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/pages/${pageId}/ai-analysis`,
    {
      method: "POST",
      ...jsonBody(
        payload ?? {
          provider: "openai",
          depth: "standard",
          includeSeo: true,
          includeGeo: true,
          includeCro: true,
          includeAdsReadiness: true,
        },
      ),
    },
  );
}

export function analyzeGrowthAuditPagePerformance(
  projectId: string,
  runId: string,
  pageId: string,
  payload?: GrowthAuditPagePerformanceAnalysisRequest,
): Promise<GrowthAuditPagePerformanceAnalysisResponse> {
  return apiFetch<GrowthAuditPagePerformanceAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/pages/${pageId}/performance-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? { strategy: "mobile" }),
    },
  );
}

export function analyzeGrowthAuditSearchConsole(
  projectId: string,
  runId: string,
  payload?: GrowthAuditSearchConsoleAnalysisRequest,
): Promise<GrowthAuditSearchConsoleAnalysisResponse> {
  return apiFetch<GrowthAuditSearchConsoleAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/search-console-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? { days: 28 }),
    },
  );
}

export function analyzeGrowthAuditAnalytics(
  projectId: string,
  runId: string,
  payload?: GrowthAuditAnalyticsAnalysisRequest,
): Promise<GrowthAuditAnalyticsAnalysisResponse> {
  return apiFetch<GrowthAuditAnalyticsAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/analytics-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? { days: 28 }),
    },
  );
}

export function analyzeGrowthAuditShopifyCommerce(
  projectId: string,
  runId: string,
  payload?: GrowthAuditShopifyCommerceAnalysisRequest,
): Promise<GrowthAuditShopifyCommerceAnalysisResponse> {
  return apiFetch<GrowthAuditShopifyCommerceAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/shopify-commerce-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? { days: 30 }),
    },
  );
}

export function analyzeGrowthAuditGa4Ecommerce(
  projectId: string,
  runId: string,
  payload?: GrowthAuditGa4EcommerceAnalysisRequest,
): Promise<GrowthAuditGa4EcommerceAnalysisResponse> {
  return apiFetch<GrowthAuditGa4EcommerceAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/analytics-ecommerce-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? { days: 30 }),
    },
  );
}

export function analyzeGrowthAuditMerchantCenter(
  projectId: string,
  runId: string,
  payload?: GrowthAuditMerchantCenterAnalysisRequest,
): Promise<GrowthAuditMerchantCenterAnalysisResponse> {
  return apiFetch<GrowthAuditMerchantCenterAnalysisResponse>(
    `${growthAuditBasePath(projectId)}/runs/${runId}/merchant-center-analysis`,
    {
      method: "POST",
      ...jsonBody(payload ?? {}),
    },
  );
}

export function fetchGrowthAuditPageResults(
  projectId: string,
  runId: string,
  pageId: string,
  filters?: { resultType?: string },
): Promise<GrowthAuditPageResultsListResponse> {
  const params = new URLSearchParams();
  if (filters?.resultType) {
    params.set("resultType", filters.resultType);
  }
  const query = params.toString();
  const path = `${growthAuditBasePath(projectId)}/runs/${runId}/pages/${pageId}/results${
    query ? `?${query}` : ""
  }`;
  return apiFetch<GrowthAuditPageResultsListResponse>(path);
}
