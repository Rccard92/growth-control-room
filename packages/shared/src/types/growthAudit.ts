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
  | "images"
  | "content"
  | "geo"
  | "cro"
  | "ads";

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
  aiPagesAnalyzed?: number;
  geoFindings?: number;
  croFindings?: number;
  adsFindings?: number;
  lastAiAnalysisAt?: string | null;
  lastAiAnalysisUrl?: string | null;
  performancePagesAnalyzed?: number;
  averagePerformanceScore?: number | null;
  performanceIssuesOpen?: number;
  lastPerformanceAnalysisAt?: string | null;
  lastPerformanceAnalysisUrl?: string | null;
  searchConsole?: GrowthAuditRunSearchConsoleSummary;
  analytics?: GrowthAuditRunAnalyticsSummary;
  shopifyCommerce?: GrowthAuditRunShopifyCommerceSummary;
  ga4Ecommerce?: GrowthAuditRunGa4EcommerceSummary;
}

export interface GrowthAuditRunAnalyticsSummary {
  totalSessions?: number;
  totalUsers?: number;
  averageEngagementRate?: number;
  totalConversions?: number;
  totalRevenue?: number;
  pagesWithData?: number;
  lowEngagementPages?: number;
  highTrafficLowConversionPages?: number;
  lastSyncedAt?: string | null;
}

export interface GrowthAuditRunSearchConsoleSummary {
  totalClicks?: number;
  totalImpressions?: number;
  averageCtr?: number;
  averagePosition?: number;
  pagesWithData?: number;
  opportunityPages?: number;
  lastSyncedAt?: string | null;
}

export interface GrowthAuditPageSearchConsoleQuery {
  query: string;
  clicks?: number;
  impressions?: number;
  ctr?: number;
  position?: number;
}

export interface GrowthAuditPageSearchConsoleMetadata {
  clicks?: number;
  impressions?: number;
  ctr?: number;
  position?: number;
  topQueries?: GrowthAuditPageSearchConsoleQuery[];
  syncedAt?: string;
}

export interface GrowthAuditPageAnalyticsMetadata {
  sessions?: number;
  totalUsers?: number;
  engagedSessions?: number;
  engagementRate?: number;
  averageSessionDuration?: number;
  conversions?: number;
  revenue?: number;
  source?: string;
  periodDays?: number;
  syncedAt?: string;
}

export interface GrowthAuditPageShopifyCommerceMetadata {
  periodDays?: number;
  quantitySold?: number;
  ordersCount?: number;
  sales?: number;
  currency?: string;
  averageUnitPrice?: number;
  averageOrderValue?: number;
  stock?: number | null;
  availableForSale?: boolean | null;
  productStatus?: string | null;
  priceMin?: number | null;
  priceMax?: number | null;
  syncedAt?: string;
}

export interface GrowthAuditRunShopifyCommerceSummary {
  periodDays?: number;
  totalSales?: number;
  totalQuantitySold?: number;
  productsWithSales?: number;
  productsWithoutSales?: number;
  productsOutOfStock?: number;
  currency?: string;
  topProducts?: Array<{
    pageId: string;
    productGid?: string | null;
    title?: string | null;
    sales?: number;
    quantitySold?: number;
    ordersCount?: number;
  }>;
  lastSyncedAt?: string | null;
}

export interface GrowthAuditGa4MatchCandidateItem {
  itemId?: string;
  itemName?: string;
  itemVariant?: string;
  itemsViewed?: number;
  itemsAddedToCart?: number;
  itemsPurchased?: number;
  itemRevenue?: number;
  candidateReason?: string;
}

export interface GrowthAuditGa4MatchShopifyKeys {
  productGid?: string;
  productLegacyId?: string | null;
  variantLegacyIds?: string[];
  skus?: string[];
  titleNormalized?: string;
  handleNormalized?: string;
}

export interface GrowthAuditGa4MatchDebug {
  shopifyKeys: GrowthAuditGa4MatchShopifyKeys;
  matchedBy?: string;
  matchStatus: "matched" | "no_reliable_match" | "ambiguous_match";
  reason: string;
  candidateItems: GrowthAuditGa4MatchCandidateItem[];
}

export interface GrowthAuditPageGa4EcommerceMetadata {
  periodDays?: number;
  itemViews?: number;
  itemViewEvents?: number;
  itemsAddedToCart?: number;
  itemsCheckedOut?: number;
  itemsPurchased?: number;
  itemRevenue?: number;
  currency?: string;
  viewToCartRate?: number;
  cartToCheckoutRate?: number;
  checkoutToPurchaseRate?: number;
  viewToPurchaseRate?: number;
  cartToPurchaseRate?: number;
  dropoffViewToCart?: number;
  dropoffCartToCheckout?: number;
  dropoffCheckoutToPurchase?: number;
  matchedBy?: string;
  matchedItemIds?: string[];
  matchedItemNames?: string[];
  matchDebug?: GrowthAuditGa4MatchDebug;
  source?: string;
  syncedAt?: string;
}

export interface GrowthAuditRunGa4EcommerceSummary {
  periodDays?: number;
  totalItemViews?: number;
  totalItemsAddedToCart?: number;
  totalItemsCheckedOut?: number;
  totalItemsPurchased?: number;
  totalItemRevenue?: number;
  averageViewToCartRate?: number;
  averageCartToPurchaseRate?: number;
  productsWithFunnelData?: number;
  productsWithoutFunnelData?: number;
  unmatchedItems?: number;
  matchedProducts?: number;
  productsWithNoReliableMatch?: number;
  ambiguousItemsCount?: number;
  matchingMode?: string;
  matchingWarning?: string;
  highViewLowCartProducts?: number;
  highCartLowPurchaseProducts?: number;
  topFunnelProducts?: Array<{
    pageId: string;
    title?: string | null;
    itemViews?: number;
    itemsAddedToCart?: number;
    itemsPurchased?: number;
    itemRevenue?: number;
  }>;
  lastSyncedAt?: string | null;
  currency?: string;
}

export interface GrowthAuditPageAiMetadata {
  latestResultId?: string;
  latestScore?: number;
  seoScore?: number;
  geoScore?: number;
  croScore?: number;
  adsReadinessScore?: number;
  analyzedAt?: string;
}

export interface GrowthAuditPagePerformanceMetadata {
  latestResultId?: string;
  latestScore?: number;
  analyzedAt?: string;
  cruxSource?: string | null;
  lcp?: number | null;
  cls?: number | null;
  inp?: number | null;
  strategy?: string;
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

export type GrowthAuditSourceEntityType =
  | "shopify_product"
  | "shopify_collection"
  | "shopify_page"
  | "shopify_article";

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
  sourceEntityType?: GrowthAuditSourceEntityType | string | null;
  sourceEntityId?: string | null;
  sourceEntityGid?: string | null;
  sourceEntityHandle?: string | null;
  sourceEntityTitle?: string | null;
  sourceEntitySyncedAt?: string | null;
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

export type GrowthAuditAiAnalysisDepth = "standard" | "deep";

export interface GrowthAuditPageResult {
  id: string;
  runId: string;
  pageId: string;
  projectId: string;
  resultType: string;
  skillKey?: string | null;
  status: string;
  score?: number | null;
  summary?: string | null;
  findings?: Array<Record<string, unknown>> | null;
  recommendations?: Array<Record<string, unknown>> | null;
  tasks?: Array<Record<string, unknown>> | null;
  artifacts?: Record<string, unknown> | null;
  rawOutput?: Record<string, unknown> | null;
  errorMessage?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface GrowthAuditPageAiAnalysisRequest {
  provider?: GrowthAuditProvider;
  depth?: GrowthAuditAiAnalysisDepth;
  includeSeo?: boolean;
  includeGeo?: boolean;
  includeCro?: boolean;
  includeAdsReadiness?: boolean;
  note?: string | null;
}

export interface GrowthAuditPageAiAnalysisResponse {
  run: GrowthAuditRun;
  page: GrowthAuditPage;
  result: GrowthAuditPageResult;
  findingsCount: number;
  tasksCount: number;
  message: string;
}

export interface GrowthAuditPagePerformanceAnalysisRequest {
  strategy?: "mobile" | "desktop";
}

export interface GrowthAuditPagePerformanceAnalysisResponse {
  run: GrowthAuditRun;
  page: GrowthAuditPage;
  result: GrowthAuditPageResult;
  findingsCount: number;
  tasksCount: number;
  message: string;
}

export interface GrowthAuditSearchConsoleAnalysisRequest {
  days?: number;
}

export interface GrowthAuditSearchConsoleAnalysisResponse {
  run: GrowthAuditRun;
  summary: GrowthAuditRunSearchConsoleSummary;
  message: string;
}

export interface GrowthAuditAnalyticsAnalysisRequest {
  days?: number;
}

export interface GrowthAuditAnalyticsAnalysisResponse {
  run: GrowthAuditRun;
  summary: GrowthAuditRunAnalyticsSummary;
  message: string;
}

export interface GrowthAuditShopifyCommerceAnalysisRequest {
  days?: number;
}

export interface GrowthAuditShopifyCommerceAnalysisResponse {
  run: GrowthAuditRun;
  summary: GrowthAuditRunShopifyCommerceSummary;
  message: string;
}

export interface GrowthAuditGa4EcommerceAnalysisRequest {
  days?: number;
}

export interface GrowthAuditGa4EcommerceAnalysisResponse {
  run: GrowthAuditRun;
  summary: GrowthAuditRunGa4EcommerceSummary;
  message: string;
}

export interface GrowthAuditPageResultsListResponse {
  results: GrowthAuditPageResult[];
}
