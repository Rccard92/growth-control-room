import type {
  DataForSeoEstimateRequest,
  DataForSeoEstimateResponse,
  DataForSeoStatus,
  DataForSeoTestRequest,
  DataForSeoTestResponse,
  DataForSeoUsageResponse,
} from "@gcr/shared";
import { apiFetch, jsonBody } from "./api";

export function fetchDataForSeoStatus(projectId: string): Promise<DataForSeoStatus> {
  return apiFetch<DataForSeoStatus>(`/api/projects/${projectId}/dataforseo/status`);
}

export function estimateDataForSeoCost(
  projectId: string,
  payload: DataForSeoEstimateRequest,
): Promise<DataForSeoEstimateResponse> {
  return apiFetch<DataForSeoEstimateResponse>(
    `/api/projects/${projectId}/dataforseo/cost-sandbox/estimate`,
    {
      method: "POST",
      ...jsonBody(payload),
    },
  );
}

export function runDataForSeoSandboxTest(
  projectId: string,
  payload: DataForSeoTestRequest,
): Promise<DataForSeoTestResponse> {
  return apiFetch<DataForSeoTestResponse>(
    `/api/projects/${projectId}/dataforseo/cost-sandbox/test`,
    {
      method: "POST",
      ...jsonBody(payload),
    },
  );
}

export function fetchDataForSeoUsage(projectId: string): Promise<DataForSeoUsageResponse> {
  return apiFetch<DataForSeoUsageResponse>(`/api/projects/${projectId}/dataforseo/usage`);
}
