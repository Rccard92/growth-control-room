import type {
  AiUsageFilters,
  DateRangeParams,
  GrowthAuditFindingsFilters,
  GrowthAuditTasksFilters,
} from "@gcr/shared";

export const queryKeys = {
  projects: {
    all: ["projects"] as const,
    detail: (id: string) => ["projects", id] as const,
    integrations: (id: string) => ["projects", id, "integrations"] as const,
  },
  google: {
    status: (projectId: string) => ["google", projectId, "status"] as const,
    searchConsoleSites: (projectId: string) =>
      ["google", projectId, "search-console-sites"] as const,
    analyticsProperties: (projectId: string) =>
      ["google", projectId, "analytics-properties"] as const,
    merchantAccounts: (projectId: string) =>
      ["google", projectId, "merchant-accounts"] as const,
  },
  shopify: {
    status: (projectId: string) => ["shopify", projectId, "status"] as const,
    scopes: (projectId: string) => ["shopify", projectId, "scopes"] as const,
    dashboard: (projectId: string, dateRange?: DateRangeParams) =>
      [
        "shopify",
        projectId,
        "dashboard",
        dateRange?.range ?? null,
        dateRange?.startDate ?? null,
        dateRange?.endDate ?? null,
      ] as const,
    products: (projectId: string) => ["shopify", projectId, "products"] as const,
    orders: (projectId: string) => ["shopify", projectId, "orders"] as const,
  },
  contentSeo: {
    dashboard: (projectId: string) => ["contentSeo", projectId, "dashboard"] as const,
    products: (projectId: string) => ["contentSeo", projectId, "products"] as const,
    collections: (projectId: string) => ["contentSeo", projectId, "collections"] as const,
    proposals: (projectId: string) => ["contentSeo", projectId, "proposals"] as const,
    productAnalysis: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "productAnalysis", entityId] as const,
    collectionAnalysis: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "collectionAnalysis", entityId] as const,
    productDetail: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "productDetail", entityId] as const,
    collectionDetail: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "collectionDetail", entityId] as const,
    proposalDetail: (projectId: string, proposalId: string) =>
      ["contentSeo", projectId, "proposal", proposalId] as const,
    proposalPreview: (projectId: string, proposalId: string) =>
      ["contentSeo", projectId, "proposalPreview", proposalId] as const,
    editorialItems: (projectId: string, month?: string) =>
      ["contentSeo", projectId, "editorialItems", month ?? "all"] as const,
    editorialBriefJob: (projectId: string, jobId: string) =>
      ["contentSeo", projectId, "editorialBriefJob", jobId] as const,
    shopifyBlogs: (projectId: string) =>
      ["contentSeo", projectId, "shopifyBlogs"] as const,
  },
  brandIntelligence: {
    overview: (projectId: string) => ["brandIntelligence", projectId, "overview"] as const,
    score: (projectId: string) => ["brandIntelligence", projectId, "score"] as const,
    context: (projectId: string) => ["brandIntelligence", projectId, "context"] as const,
    profile: (projectId: string) => ["brandIntelligence", projectId, "profile"] as const,
    identity: (projectId: string) => ["brandIntelligence", projectId, "identity"] as const,
    visualIdentity: (projectId: string) =>
      ["brandIntelligence", projectId, "visualIdentity"] as const,
    safeClaims: (projectId: string) => ["brandIntelligence", projectId, "safeClaims"] as const,
    faqObjections: (projectId: string) =>
      ["brandIntelligence", projectId, "faqObjections"] as const,
    editorialGuidelines: (projectId: string) =>
      ["brandIntelligence", projectId, "editorialGuidelines"] as const,
    productKnowledgeGeneral: (projectId: string) =>
      ["brandIntelligence", projectId, "productKnowledgeGeneral"] as const,
    productKnowledgeItems: (projectId: string) =>
      ["brandIntelligence", projectId, "productKnowledgeItems"] as const,
    productKnowledgeShopifyProducts: (projectId: string) =>
      ["brandIntelligence", projectId, "productKnowledgeShopifyProducts"] as const,
    voice: (projectId: string) => ["brandIntelligence", projectId, "voice"] as const,
    products: (projectId: string) => ["brandIntelligence", projectId, "products"] as const,
    audience: (projectId: string) => ["brandIntelligence", projectId, "audience"] as const,
    claims: (projectId: string) => ["brandIntelligence", projectId, "claims"] as const,
    seoStrategy: (projectId: string) =>
      ["brandIntelligence", projectId, "seoStrategy"] as const,
    pillars: (projectId: string) => ["brandIntelligence", projectId, "pillars"] as const,
    guardrails: (projectId: string) => ["brandIntelligence", projectId, "guardrails"] as const,
    assets: (projectId: string) => ["brandIntelligence", projectId, "assets"] as const,
    sources: (projectId: string) => ["brandIntelligence", projectId, "sources"] as const,
    extractedFacts: (projectId: string, filters?: Record<string, string | undefined>) =>
      ["brandIntelligence", projectId, "extractedFacts", filters ?? {}] as const,
    importBatch: (projectId: string, batchId: string) =>
      ["brandIntelligence", projectId, "importBatch", batchId] as const,
    importBatches: (projectId: string) =>
      ["brandIntelligence", projectId, "importBatches"] as const,
    sectionDrafts: (projectId: string, filters?: Record<string, string | undefined>) =>
      ["brandIntelligence", projectId, "sectionDrafts", filters ?? {}] as const,
    sectionDraft: (projectId: string, draftId: string) =>
      ["brandIntelligence", projectId, "sectionDraft", draftId] as const,
    briefs: (projectId: string) => ["brandIntelligence", projectId, "briefs"] as const,
    brief: (projectId: string, briefId: string) =>
      ["brandIntelligence", projectId, "brief", briefId] as const,
  },
  health: ["health"] as const,
  aiUsage: {
    summary: (projectId: string, filters?: AiUsageFilters) =>
      ["aiUsage", projectId, "summary", filters ?? {}] as const,
    logs: (projectId: string, filters?: AiUsageFilters) =>
      ["aiUsage", projectId, "logs", filters ?? {}] as const,
    logDetail: (projectId: string, logId: string) =>
      ["aiUsage", projectId, "log", logId] as const,
    budget: (projectId: string) => ["aiUsage", projectId, "budget"] as const,
    estimate: (projectId: string, operation: string, count: number) =>
      ["aiUsage", projectId, "estimate", operation, count] as const,
  },
  aiModelSettings: {
    list: (projectId: string) => ["aiModelSettings", projectId] as const,
  },
  dataforseo: {
    status: (projectId: string) => ["dataforseo", projectId, "status"] as const,
    usage: (projectId: string) => ["dataforseo", projectId, "usage"] as const,
  },
  seoSkills: {
    catalog: (projectId: string) => ["seo-skills", "catalog", projectId] as const,
    runs: (projectId: string) => ["seo-skills", "runs", projectId] as const,
    run: (projectId: string, runId: string) =>
      ["seo-skills", "run", projectId, runId] as const,
    runResults: (projectId: string, runId: string) =>
      ["seo-skills", "run-results", projectId, runId] as const,
  },
  growthAudit: {
    runs: (projectId: string) => ["growth-audit", "runs", projectId] as const,
    run: (projectId: string, runId: string) =>
      ["growth-audit", "run", projectId, runId] as const,
    pages: (projectId: string, runId: string) =>
      ["growth-audit", "pages", projectId, runId] as const,
    events: (projectId: string, runId: string) =>
      ["growth-audit", "events", projectId, runId] as const,
    findings: (projectId: string, runId: string, filters?: GrowthAuditFindingsFilters) =>
      ["growth-audit", "findings", projectId, runId, filters ?? {}] as const,
    tasks: (projectId: string, runId: string, filters?: GrowthAuditTasksFilters) =>
      ["growth-audit", "tasks", projectId, runId, filters ?? {}] as const,
    pageResults: (projectId: string, runId: string, pageId: string, resultType?: string) =>
      ["growth-audit", "page-results", projectId, runId, pageId, resultType ?? ""] as const,
  },
};
