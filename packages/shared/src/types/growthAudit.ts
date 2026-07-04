export type GrowthAuditProvider = "openai" | "claude";
export type GrowthAuditMode = "full_site_mvp";
export type GrowthAuditRunStatus =
  | "pending"
  | "queued"
  | "discovering"
  | "classifying"
  | "analyzing"
  | "ready_for_analysis"
  | "completed"
  | "failed"
  | "partial_failed"
  | "cancelled";
export type GrowthAuditPhase =
  | "queued"
  | "discovery"
  | "classification"
  | "analysis"
  | "technical_scan"
  | "page_rescan"
  | "ready_for_analysis"
  | "finalization"
  | "completed"
  | "failed";
export type GrowthAuditPageType =
  | "homepage"
  | "product"
  | "collection"
  | "blog"
  | "blog_article"
  | "article"
  | "static_page"
  | "page"
  | "policy"
  | "cart"
  | "checkout"
  | "search"
  | "account"
  | "other"
  | "unknown";
export type GrowthAuditPageStatus =
  | "pending"
  | "discovered"
  | "classified"
  | "analyzing"
  | "analyzed"
  | "failed"
  | "skipped";
export type GrowthAuditPageSource =
  | "seed"
  | "sitemap"
  | "shopify_product"
  | "shopify_collection"
  | "shopify_page"
  | "shopify_blog"
  | "crawl"
  | "manual";

export type GrowthAuditInventoryFilter =
  | "all"
  | "homepage"
  | "product"
  | "collection"
  | "blog"
  | "static_page"
  | "unknown";

export type GrowthAuditScoreFilter = "all" | "critical" | "warning" | "good";

export type GrowthAuditPageStatusFilter = "all" | "analyzed" | "failed";

export type GrowthAuditFindingSeverity =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "info";

export type GrowthAuditFindingCategory =
  | "technical"
  | "seo"
  | "schema"
  | "images";

export type GrowthAuditTaskOwnerType = "seo" | "content" | "dev" | "design" | "ads";

export type GrowthAuditFindingStatus = "open" | "completed" | "dismissed" | "superseded";

export type GrowthAuditTaskStatus = "open" | "completed" | "dismissed" | "superseded";

export interface GrowthAuditRunSummary {
  message?: string;
  pagesDiscovered?: number;
  pagesClassified?: number;
  pagesAnalyzed?: number;
  pagesFailed?: number;
  averageTechnicalScore?: number | null;
  criticalFindings?: number;
  highFindings?: number;
  tasksOpen?: number;
  includeAiAnalysis?: boolean;
  auditMode?: string;
  sources?: {
    seed?: number;
    sitemap?: number;
    shopify?: number;
  };
  pageTypes?: Record<string, number>;
  nextStep?: string;
  warning?: string | null;
  lastPageRescanAt?: string | null;
}

export interface GrowthAuditRunCreateRequest {
  rootUrl: string;
  provider?: GrowthAuditProvider;
  auditMode?: GrowthAuditMode;
  maxPages?: number;
  includeAiAnalysis?: boolean;
}

export interface GrowthAuditRun {
  id: string;
  projectId: string;
  rootUrl: string;
  normalizedDomain: string;
  status: GrowthAuditRunStatus;
  phase?: string | null;
  auditMode: string;
  provider: GrowthAuditProvider;
  progressPercent: number;
  pagesDiscovered: number;
  pagesClassified: number;
  pagesAnalyzed: number;
  pagesFailed: number;
  totalPages?: number | null;
  currentUrl?: string | null;
  config?: Record<string, unknown> | null;
  summary?: GrowthAuditRunSummary | null;
  siteScore?: number | null;
  seoScore?: number | null;
  geoScore?: number | null;
  croScore?: number | null;
  performanceScore?: number | null;
  errorMessage?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GrowthAuditPage {
  id: string;
  runId: string;
  projectId: string;
  url: string;
  normalizedUrl: string;
  path?: string | null;
  pageType: GrowthAuditPageType | string;
  source: GrowthAuditPageSource | string;
  status: GrowthAuditPageStatus | string;
  priority: string;
  title?: string | null;
  metaDescription?: string | null;
  canonicalUrl?: string | null;
  h1?: string | null;
  httpStatus?: number | null;
  depth?: number | null;
  score?: number | null;
  seoScore?: number | null;
  geoScore?: number | null;
  croScore?: number | null;
  performanceScore?: number | null;
  discoveredAt?: string | null;
  classifiedAt?: string | null;
  analyzedAt?: string | null;
  errorMessage?: string | null;
  metadata?: Record<string, unknown> | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GrowthAuditEvent {
  id: string;
  runId: string;
  projectId: string;
  eventType: string;
  phase?: string | null;
  message: string;
  progressPercent?: number | null;
  payload?: Record<string, unknown> | null;
  createdAt?: string | null;
}

export interface GrowthAuditInventoryCounts {
  total: number;
  homepage: number;
  product: number;
  collection: number;
  blog: number;
  staticPage: number;
  unknown: number;
  bySource: Record<string, number>;
  byStatus: Record<string, number>;
}

export interface GrowthAuditRunDetailResponse {
  run: GrowthAuditRun;
  pages: GrowthAuditPage[];
  events: GrowthAuditEvent[];
  findingsCount: number;
  tasksCount: number;
}

export interface GrowthAuditRunsListResponse {
  runs: GrowthAuditRun[];
}

export interface GrowthAuditPagesListResponse {
  pages: GrowthAuditPage[];
}

export interface GrowthAuditEventsListResponse {
  events: GrowthAuditEvent[];
}

export interface GrowthAuditStartResponse {
  run: GrowthAuditRun;
}

export interface GrowthAuditFinding {
  id: string;
  runId: string;
  pageId?: string | null;
  projectId: string;
  sourceResultId?: string | null;
  category: GrowthAuditFindingCategory | string;
  severity: GrowthAuditFindingSeverity | string;
  priority: string;
  title: string;
  description?: string | null;
  evidence?: string | null;
  recommendation?: string | null;
  howToValidate?: string | null;
  impact?: string | null;
  effort?: string | null;
  status: string;
  metadata?: Record<string, unknown> | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GrowthAuditTask {
  id: string;
  runId: string;
  pageId?: string | null;
  findingId?: string | null;
  projectId: string;
  title: string;
  description?: string | null;
  ownerType: GrowthAuditTaskOwnerType | string;
  priority: string;
  estimatedEffort: string;
  status: string;
  metadata?: Record<string, unknown> | null;
  completedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GrowthAuditFindingsListResponse {
  findings: GrowthAuditFinding[];
}

export interface GrowthAuditTasksListResponse {
  tasks: GrowthAuditTask[];
}

export interface GrowthAuditFindingsFilters {
  pageId?: string;
  severity?: string;
  category?: string;
  status?: string;
}

export interface GrowthAuditTasksFilters {
  pageId?: string;
  priority?: string;
  ownerType?: string;
  status?: string;
}

export interface GrowthAuditPageRescanRequest {
  clearPreviousOpenItems?: boolean;
  note?: string | null;
}

export interface GrowthAuditPageRescanResponse {
  run: GrowthAuditRun;
  page: GrowthAuditPage;
  findingsCount: number;
  tasksCount: number;
  message: string;
}
