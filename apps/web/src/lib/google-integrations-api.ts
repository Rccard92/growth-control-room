import type {
  GoogleIntegrationStatusResponse,
  GoogleOAuthStartRequest,
  GoogleOAuthStartResponse,
  GoogleSearchConsoleSitesResponse,
  SelectSearchConsoleSiteRequest,
  SelectSearchConsoleSiteResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

export function fetchGoogleIntegrationStatus(
  projectId: string,
): Promise<GoogleIntegrationStatusResponse> {
  return apiFetch<GoogleIntegrationStatusResponse>(`/api/projects/${projectId}/google/status`);
}

export function fetchSearchConsoleSites(
  projectId: string,
): Promise<GoogleSearchConsoleSitesResponse> {
  return apiFetch<GoogleSearchConsoleSitesResponse>(
    `/api/projects/${projectId}/google/search-console/sites`,
  );
}

export function selectSearchConsoleSite(
  projectId: string,
  payload: SelectSearchConsoleSiteRequest,
): Promise<SelectSearchConsoleSiteResponse> {
  return apiFetch<SelectSearchConsoleSiteResponse>(
    `/api/projects/${projectId}/google/search-console/select-site`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export function startGoogleOAuth(
  projectId: string,
  payload?: GoogleOAuthStartRequest,
): Promise<GoogleOAuthStartResponse> {
  return apiFetch<GoogleOAuthStartResponse>(`/api/projects/${projectId}/google/oauth/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? { services: ["search_console", "analytics", "google_ads"] }),
  });
}
