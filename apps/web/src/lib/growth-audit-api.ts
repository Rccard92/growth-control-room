import type {
  GrowthAuditEventsListResponse,
  GrowthAuditPagesListResponse,
  GrowthAuditRunCreateRequest,
  GrowthAuditRunDetailResponse,
  GrowthAuditRunsListResponse,
  GrowthAuditStartResponse,
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
