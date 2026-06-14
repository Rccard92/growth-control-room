import type { DateRangeParams } from "./date-range";

export interface AiUsageBreakdownItem {
  key?: string;
  date?: string;
  requests: number;
  estimatedCost: number;
  inputTokens?: number;
}

export interface AiUsageSummary {
  totalEstimatedCost: number;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCachedInputTokens: number;
  byModule: AiUsageBreakdownItem[];
  byOperation: AiUsageBreakdownItem[];
  byModel: AiUsageBreakdownItem[];
  byDay: AiUsageBreakdownItem[];
  projectCount?: number;
}

export interface AiUsageLog {
  id: string;
  projectId: string | null;
  provider: string;
  model: string;
  module: string;
  operation: string;
  entityType: string | null;
  entityId: string | null;
  jobId: string | null;
  status: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cachedInputTokens: number;
  reasoningTokens: number;
  estimatedInputCost: number | null;
  estimatedOutputCost: number | null;
  estimatedCachedCost: number | null;
  estimatedTotalCost: number | null;
  durationMs: number | null;
  promptChars: number | null;
  outputChars: number | null;
  promptHash: string | null;
  promptPreview: string | null;
  outputPreview: string | null;
  promptCacheKey: string | null;
  contextProfile: string | null;
  contextHash: string | null;
  contextChars: number | null;
  contextBlocksUsed: string[] | null;
  responseId: string | null;
  errorType: string | null;
  errorMessage: string | null;
  createdAt: string;
}

export interface AiUsageLogListResponse {
  items: AiUsageLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface AiBudgetStatus {
  dailySpent: number;
  monthlySpent: number;
  dailyBudgetUsd: number | null;
  monthlyBudgetUsd: number | null;
  nearLimit: boolean;
  blocked: boolean;
}

export interface AiUsageEstimate {
  operation: string;
  count: number;
  estimatedTotalCost: number | null;
  avgCostPerRequest: number | null;
  basedOnRequests: number;
  message: string | null;
}

export interface AiUsageFilters {
  dateRange?: DateRangeParams;
  module?: string;
  operation?: string;
  model?: string;
  status?: string;
  limit?: number;
  offset?: number;
}
