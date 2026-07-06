export interface DataForSeoStatus {
  configured: boolean;
  realCallsEnabled: boolean;
  missingVars: string[];
  singleRunLimitUsd: number;
  dailyBudgetUsd: number;
  monthlyBudgetUsd: number;
  usageTodayUsd: number;
  usageMonthUsd: number;
  account?: {
    balanceUsd?: number | null;
    totalDepositedUsd?: number | null;
  } | null;
}

export type DataForSeoEstimateMode = "single_page" | "top_10_products" | "full_site";

export type DataForSeoTestType =
  | "search_volume"
  | "search_volume_batch"
  | "keyword_ideas"
  | "serp"
  | "micro_bundle";

export interface DataForSeoEstimateRequest {
  mode: DataForSeoEstimateMode;
  runId?: string;
  productPagesCount?: number;
  seedQueriesPerPage?: number;
  keywordIdeasPerSeed?: number;
  serpQueriesPerPage?: number;
}

export interface DataForSeoEstimatedCalls {
  searchVolume: number;
  keywordIdeas: number;
  serp: number;
}

export interface DataForSeoObservedUnitCosts {
  searchVolume?: number | null;
  keywordIdeas?: number | null;
  serp?: number | null;
}

export interface DataForSeoEstimateResponse {
  mode: DataForSeoEstimateMode;
  estimatedCalls: DataForSeoEstimatedCalls;
  estimatedCostUsd: number;
  assumptions: string[];
  budgetWarnings: string[];
  auditContext?: {
    productPagesCount?: number;
    pagesWithGscQueries?: number;
    avgQueriesPerPage?: number;
  } | null;
  estimateSource?: "observed" | "assumed";
  observedUnitCosts?: DataForSeoObservedUnitCosts;
}

export interface DataForSeoTestRequest {
  testType: DataForSeoTestType;
  keyword?: string;
  keywords?: string[];
  locationCode?: number;
  languageCode?: string;
}

export interface SearchVolumeTrend {
  direction?: "up" | "down" | "stable" | "unknown" | string;
  lastMonth?: number | null;
  previousMonth?: number | null;
  averageLast12Months?: number | null;
}

export interface SearchVolumeResult {
  keyword: string;
  searchVolume?: number | null;
  cpc?: number | null;
  competition?: number | null;
  competitionIndex?: number | null;
  monthlySearches?: Array<{
    year?: number | null;
    month?: number | null;
    searchVolume?: number | null;
  }> | null;
  trend?: SearchVolumeTrend | null;
}

export interface DataForSeoTestResponse {
  testType: DataForSeoTestType;
  keyword: string;
  keywords?: string[];
  costUsd: number;
  averageCostPerKeywordUsd?: number | null;
  endpoints: string[];
  responseSummary?: Record<string, unknown> | null;
  rawPreview?: Record<string, unknown> | null;
}

export interface DataForSeoUsageLog {
  id: string;
  endpoint: string;
  operation: string;
  status: string;
  costUsd: number | null;
  itemsCount?: number | null;
  metadata?: Record<string, unknown> | null;
  responseSummary?: Record<string, unknown> | null;
  errorMessage?: string | null;
  createdAt: string;
}

export interface DataForSeoUsageResponse {
  logs: DataForSeoUsageLog[];
  usageTodayUsd: number;
  usageMonthUsd: number;
  averageCostByOperation: Record<string, number>;
}
