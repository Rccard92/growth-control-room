import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AiModelSettingUpdateInput } from "@gcr/shared";
import {
  getAiModelSettings,
  resetAiModelSetting,
  updateAiModelSetting,
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
