export type AiModelUiCategory =
  | "brand_intelligence"
  | "product_collection_seo"
  | "blog_articles"
  | "ped_social"
  | "email_ads"
  | "seo_advanced";

export interface AiModelSettingItem {
  operationKey: string;
  label: string;
  status: "implemented" | "planned" | "non_ai";
  enabled: boolean;
  module: string;
  contextProfile: string;
  recommendedTier: string;
  recommendedModel: string | null;
  recommendedMaxOutputTokens: number;
  recommendedTemperature: number;
  recommendedUse: string;
  qualityLevel: string;
  costSensitivity: string;
  description: string;
  warningNotes: string | null;
  model: string | null;
  modelTier: string;
  maxOutputTokens: number | null;
  temperature: number | null;
  fallbackModel: string | null;
  allowFallback: boolean;
  reasoningEffort: string | null;
  notes: string | null;
  source: string;
  hasProjectOverride: boolean;
  guardrailWarnings: string[];
  recentRequestCount: number;
  avgCostRecent: number | null;
  lastRequestAt: string | null;
  uiCategory: AiModelUiCategory;
  gcrRecommendedModel: string;
  gcrRecommendationReason: string;
  costProfileLabel: string;
}

export interface AiAvailableModelItem {
  name: string;
  pricingConfigured: boolean;
  source: string;
}

export interface AiAvailableModelsResponse {
  envModels: Record<string, string | null>;
  models: AiAvailableModelItem[];
  warnings: string[];
}

export interface AiModelSettingsListResponse {
  items: AiModelSettingItem[];
  registryCount: number;
  missingSettings: string[];
  unpricedModels: string[];
  availableModels: AiAvailableModelsResponse;
}

export interface AiModelSettingUpdateInput {
  model?: string;
  modelTier?: string;
  maxOutputTokens?: number;
  temperature?: number;
  fallbackModel?: string;
  allowFallback?: boolean;
  enabled?: boolean;
  notes?: string;
  reasoningEffort?: string;
}

export interface AiModelSettingMutationResponse {
  operationKey: string;
  model: string;
  modelTier: string;
  source: string;
  message: string | null;
}

export interface AiBulkActionResponse {
  updatedCount: number;
  message: string;
}
