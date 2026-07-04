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
  | "ready_for_analysis"
  | "completed"
  | "failed";
export type GrowthAuditPageType =
  | "homepage"
  | "product"
  | "collection"
  | "blog"
  | "article"
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
  | "analyzed"
  | "failed"
  | "skipped";
export type GrowthAuditPageSource = "seed" | "sitemap" | "crawl" | "manual";

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
  summary?: Record<string, unknown> | null;
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
  pageType: string;
  source: string;
  status: string;
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
