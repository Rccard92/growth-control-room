import type {
  AiAvailableModelsResponse,
  AiBulkActionResponse,
  AiModelSettingMutationResponse,
  AiModelSettingsListResponse,
  AiModelSettingUpdateInput,
  AiModelValidateInput,
  AiModelValidateResponse,
} from "@gcr/shared";
import { apiFetch, jsonBody } from "./api";

export function getAiModelSettings(projectId: string): Promise<AiModelSettingsListResponse> {
  return apiFetch<AiModelSettingsListResponse>(
    `/api/projects/${projectId}/ai-model-settings`,
  );
}

export function updateAiModelSetting(
  projectId: string,
  operationKey: string,
  body: AiModelSettingUpdateInput,
): Promise<AiModelSettingMutationResponse> {
  return apiFetch<AiModelSettingMutationResponse>(
    `/api/projects/${projectId}/ai-model-settings/${operationKey}`,
    { method: "PUT", ...jsonBody(body) },
  );
}

export function resetAiModelSetting(
  projectId: string,
  operationKey: string,
): Promise<AiModelSettingMutationResponse> {
  return apiFetch<AiModelSettingMutationResponse>(
    `/api/projects/${projectId}/ai-model-settings/${operationKey}/reset`,
    { method: "POST" },
  );
}

export function applyGcrRecommendations(projectId: string): Promise<AiBulkActionResponse> {
  return apiFetch<AiBulkActionResponse>(
    `/api/projects/${projectId}/ai-model-settings/apply-gcr-recommendations`,
    { method: "POST" },
  );
}

export function resetModelsFromRailway(projectId: string): Promise<AiBulkActionResponse> {
  return apiFetch<AiBulkActionResponse>(
    `/api/projects/${projectId}/ai-model-settings/reset-railway`,
    { method: "POST" },
  );
}

export function seedAiModelDefaults(projectId: string): Promise<{
  globalCreated: number;
  projectCreated: number;
}> {
  return apiFetch(`/api/projects/${projectId}/ai-model-settings/seed-defaults`, {
    method: "POST",
  });
}

export function getAvailableAiModels(): Promise<AiAvailableModelsResponse> {
  return apiFetch<AiAvailableModelsResponse>("/api/ai-model-settings/available-models");
}

export function validateAiModel(
  projectId: string,
  body: AiModelValidateInput,
): Promise<AiModelValidateResponse> {
  return apiFetch<AiModelValidateResponse>(
    `/api/projects/${projectId}/ai-model-settings/validate-model`,
    { method: "POST", ...jsonBody(body) },
  );
}
