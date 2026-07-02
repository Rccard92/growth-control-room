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
  defaultProvider: SeoSkillProvider | string;
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

export type SeoSkillTargetType =
  | "url"
  | "shopify_product"
  | "shopify_collection"
  | "article"
  | "domain";

export interface SeoSkillRunCreateRequest {
  targetType: SeoSkillTargetType | string;
  targetId?: string | null;
  url?: string | null;
  selectedSkills: string[];
  provider: SeoSkillProvider;
}

export interface SeoSkillRun {
  id: string;
  projectId: string;
  targetType: string;
  targetId?: string | null;
  url?: string | null;
  status: SeoSkillRunStatus;
  provider: SeoSkillProvider | string;
  selectedSkills: string[];
  progressPercent: number;
  currentSkill?: string | null;
  errorMessage?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface SeoSkillRunResult {
  id: string;
  runId: string;
  projectId: string;
  skillKey: string;
  status: SeoSkillRunResultStatus;
  score?: number | null;
  findings?: unknown[] | null;
  recommendations?: unknown[] | null;
  tasks?: unknown[] | null;
  artifacts?: Record<string, unknown> | null;
  rawOutput?: Record<string, unknown> | null;
  errorMessage?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface SeoSkillRunDetailResponse {
  run: SeoSkillRun;
  results: SeoSkillRunResult[];
}

export interface SeoSkillRunStartResponse {
  run: SeoSkillRun;
}
