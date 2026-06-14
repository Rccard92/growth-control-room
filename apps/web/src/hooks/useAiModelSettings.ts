import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AiModelSettingUpdateInput, AiModelValidateInput } from "@gcr/shared";
import {
  applyGcrRecommendations,
  getAiModelSettings,
  resetAiModelSetting,
  resetModelsFromRailway,
  updateAiModelSetting,
  validateAiModel,
} from "../lib/ai-model-settings-api";
import { queryKeys } from "../lib/queryKeys";

export function useAiModelSettings(projectId: string) {
  return useQuery({
    queryKey: queryKeys.aiModelSettings.list(projectId),
    queryFn: () => getAiModelSettings(projectId),
    enabled: Boolean(projectId),
  });
}

export function useUpdateAiModelSetting(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      operationKey,
      body,
    }: {
      operationKey: string;
      body: AiModelSettingUpdateInput;
    }) => updateAiModelSetting(projectId, operationKey, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.aiModelSettings.list(projectId) });
    },
  });
}

export function useResetAiModelSetting(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (operationKey: string) => resetAiModelSetting(projectId, operationKey),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.aiModelSettings.list(projectId) });
    },
  });
}

export function useApplyGcrRecommendations(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => applyGcrRecommendations(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.aiModelSettings.list(projectId) });
    },
  });
}

export function useResetModelsFromRailway(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => resetModelsFromRailway(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.aiModelSettings.list(projectId) });
    },
  });
}

export function useValidateAiModel(projectId: string) {
  return useMutation({
    mutationFn: (body: AiModelValidateInput) => validateAiModel(projectId, body),
  });
}
