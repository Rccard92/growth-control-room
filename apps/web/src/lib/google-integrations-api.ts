import type {
  GoogleIntegrationStatusResponse,
  GoogleOAuthStartRequest,
  GoogleOAuthStartResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

export function fetchGoogleIntegrationStatus(
  projectId: string,
): Promise<GoogleIntegrationStatusResponse> {
  return apiFetch<GoogleIntegrationStatusResponse>(`/api/projects/${projectId}/google/status`);
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
