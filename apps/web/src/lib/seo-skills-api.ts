import type {
  SeoSkillCatalogResponse,
  SeoSkillRun,
  SeoSkillRunCreateRequest,
  SeoSkillRunDetailResponse,
  SeoSkillRunResult,
  SeoSkillRunStartResponse,
} from "@gcr/shared";
import { apiFetch, jsonBody } from "./api";

function seoSkillsBasePath(projectId: string): string {
  return `/api/projects/${projectId}/seo-skills`;
}

export function fetchSeoSkillCatalog(projectId: string): Promise<SeoSkillCatalogResponse> {
  return apiFetch<SeoSkillCatalogResponse>(`${seoSkillsBasePath(projectId)}/catalog`);
}

export function startSeoSkillRun(
  projectId: string,
  payload: SeoSkillRunCreateRequest,
): Promise<SeoSkillRunStartResponse> {
  return apiFetch<SeoSkillRunStartResponse>(`${seoSkillsBasePath(projectId)}/runs`, {
    method: "POST",
    ...jsonBody(payload),
  });
}

export function listSeoSkillRuns(projectId: string, limit = 20): Promise<SeoSkillRun[]> {
  const params = new URLSearchParams();
  if (limit !== 20) {
    params.set("limit", String(limit));
  }
  const query = params.toString();
  const path = `${seoSkillsBasePath(projectId)}/runs${query ? `?${query}` : ""}`;
  return apiFetch<SeoSkillRun[]>(path);
}

export function fetchSeoSkillRun(
  projectId: string,
  runId: string,
): Promise<SeoSkillRunDetailResponse> {
  return apiFetch<SeoSkillRunDetailResponse>(
    `${seoSkillsBasePath(projectId)}/runs/${runId}`,
  );
}

export function fetchSeoSkillRunResults(
  projectId: string,
  runId: string,
): Promise<SeoSkillRunResult[]> {
  return apiFetch<SeoSkillRunResult[]>(
    `${seoSkillsBasePath(projectId)}/runs/${runId}/results`,
  );
}
