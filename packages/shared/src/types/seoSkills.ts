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
