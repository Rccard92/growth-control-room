export type SeoSkillStatus =
  | "available"
  | "needs_config"
  | "external_required"
  | "planned";

export type SeoSkillRuntime =
  | "prompt_only"
  | "connector_required"
  | "external_api_required"
  | "planned";

export type SeoSkillRiskLevel = "low" | "medium" | "high";

export type SeoSkillCategory =
  | "audit"
  | "content"
  | "structured_data"
  | "ai_search"
  | "media"
  | "sitemap"
  | "strategy"
  | "local"
  | "ecommerce"
  | "competitive"
  | "integrations"
  | string;

export interface SeoSkillCatalogItem {
  key: string;
  label: string;
  description: string;
  category: SeoSkillCategory;
  source: string;
  upstreamCommand: string;
  status: SeoSkillStatus;
  defaultProvider: string;
  requires: string[];
  optionalIntegrations: string[];
  requiredIntegrations: string[];
  outputSchema: string;
  runtime: SeoSkillRuntime;
  riskLevel: SeoSkillRiskLevel;
  enabled: boolean;
}

export interface SeoSkillCatalogCounts {
  total: number;
  available: number;
  needsConfig: number;
  externalRequired: number;
  planned: number;
}

export interface SeoSkillCatalogResponse {
  skills: SeoSkillCatalogItem[];
  counts: SeoSkillCatalogCounts;
}

export type SeoSkillProvider = "openai" | "claude";

export type SeoSkillRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "partial_failed";

export type SeoSkillRunResultStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export type SeoSkillJsonValue =
  | Record<string, unknown>
  | unknown[]
  | string
  | number
  | boolean
  | null;

export interface SeoSkillRunCreateRequest {
  targetType: string;
  targetId?: string;
  url?: string;
  selectedSkills: string[];
  provider?: SeoSkillProvider;
}

export interface SeoSkillRun {
  id: string;
  projectId: string;
  targetType: string;
  targetId?: string;
  url?: string;
  status: SeoSkillRunStatus;
  provider: SeoSkillProvider;
  selectedSkills: string[];
  progressPercent: number;
  currentSkill?: string;
  errorMessage?: string;
  startedAt?: string;
  completedAt?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface SeoSkillRunResult {
  id: string;
  runId: string;
  projectId: string;
  skillKey: string;
  status: SeoSkillRunResultStatus;
  score?: number;
  findings?: SeoSkillJsonValue;
  recommendations?: SeoSkillJsonValue;
  tasks?: SeoSkillJsonValue;
  artifacts?: SeoSkillJsonValue;
  rawOutput?: SeoSkillJsonValue;
  errorMessage?: string;
  startedAt?: string;
  completedAt?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface SeoSkillRunDetailResponse {
  run: SeoSkillRun;
  results: SeoSkillRunResult[];
}

export interface SeoSkillRunStartResponse {
  run: SeoSkillRun;
}
