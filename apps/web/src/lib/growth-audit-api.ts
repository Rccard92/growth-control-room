import type {
  GrowthAuditEventsListResponse,
  GrowthAuditFindingsFilters,
  GrowthAuditFindingsListResponse,
  GrowthAuditPageAiAnalysisRequest,
  GrowthAuditPageAiAnalysisResponse,
  GrowthAuditPageRescanRequest,
  GrowthAuditPageRescanResponse,
  GrowthAuditPageResultsListResponse,
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
