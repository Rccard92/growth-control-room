import type {
  ContentSeoAnalyzeResponse,
  ContentSeoDashboard,
  ContentSeoSyncResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

export function syncContentSeoShopify(projectId: string): Promise<ContentSeoSyncResponse> {
  return apiFetch<ContentSeoSyncResponse>(`/api/projects/${projectId}/content/seo/sync-shopify`, {
    method: "POST",
  });
}

export function analyzeContentSeo(projectId: string): Promise<ContentSeoAnalyzeResponse> {
  return apiFetch<ContentSeoAnalyzeResponse>(`/api/projects/${projectId}/content/seo/analyze`, {
    method: "POST",
  });
}

export function getContentSeoDashboard(projectId: string): Promise<ContentSeoDashboard> {
  return apiFetch<ContentSeoDashboard>(`/api/projects/${projectId}/content/seo/dashboard`);
}
