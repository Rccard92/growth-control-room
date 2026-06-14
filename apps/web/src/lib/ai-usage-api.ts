import type {
  AiBudgetStatus,
  AiUsageEstimate,
  AiUsageFilters,
  AiUsageLog,
  AiUsageLogListResponse,
  AiUsageSummary,
  DateRangeParams,
} from "@gcr/shared";
import { apiFetch } from "./api";

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function resolveDateRangeBounds(params?: DateRangeParams): {
  startDate?: string;
  endDate?: string;
} {
  if (!params) return {};
  if (params.range === "custom" && params.startDate && params.endDate) {
    return { startDate: params.startDate, endDate: params.endDate };
  }

  const today = new Date();
  const end = formatDate(today);

  switch (params.range) {
    case "today":
      return { startDate: end, endDate: end };
    case "yesterday": {
      const y = new Date(today);
      y.setDate(y.getDate() - 1);
      const ys = formatDate(y);
      return { startDate: ys, endDate: ys };
    }
    case "last_7_days": {
      const s = new Date(today);
      s.setDate(s.getDate() - 6);
      return { startDate: formatDate(s), endDate: end };
    }
    case "last_30_days": {
      const s = new Date(today);
      s.setDate(s.getDate() - 29);
      return { startDate: formatDate(s), endDate: end };
    }
    case "month_to_date": {
      const s = new Date(today.getFullYear(), today.getMonth(), 1);
      return { startDate: formatDate(s), endDate: end };
    }
    case "previous_month": {
      const s = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      const e = new Date(today.getFullYear(), today.getMonth(), 0);
      return { startDate: formatDate(s), endDate: formatDate(e) };
    }
    default:
      return {};
  }
}

function buildQuery(filters?: AiUsageFilters): string {
  const q = new URLSearchParams();
  const bounds = resolveDateRangeBounds(filters?.dateRange);
  if (bounds.startDate) q.set("startDate", bounds.startDate);
  if (bounds.endDate) q.set("endDate", bounds.endDate);
  if (filters?.module) q.set("module", filters.module);
  if (filters?.operation) q.set("operation", filters.operation);
  if (filters?.model) q.set("model", filters.model);
  if (filters?.status) q.set("status", filters.status);
  if (filters?.limit != null) q.set("limit", String(filters.limit));
  if (filters?.offset != null) q.set("offset", String(filters.offset));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function getAiUsageSummary(
  projectId: string,
  filters?: AiUsageFilters,
): Promise<AiUsageSummary> {
  return apiFetch<AiUsageSummary>(
    `/api/projects/${projectId}/ai-usage/summary${buildQuery(filters)}`,
  );
}

export function getAiUsageLogs(
  projectId: string,
  filters?: AiUsageFilters,
): Promise<AiUsageLogListResponse> {
  return apiFetch<AiUsageLogListResponse>(
    `/api/projects/${projectId}/ai-usage/logs${buildQuery({ ...filters, limit: filters?.limit ?? 50 })}`,
  );
}

export function getAiUsageLog(projectId: string, logId: string): Promise<AiUsageLog> {
  return apiFetch<AiUsageLog>(`/api/projects/${projectId}/ai-usage/logs/${logId}`);
}

export function getAiBudgetStatus(projectId: string): Promise<AiBudgetStatus> {
  return apiFetch<AiBudgetStatus>(`/api/projects/${projectId}/ai-usage/budget-status`);
}

export function getAiUsageEstimate(
  projectId: string,
  operation: string,
  count: number,
): Promise<AiUsageEstimate> {
  const q = new URLSearchParams({ operation, count: String(count) });
  return apiFetch<AiUsageEstimate>(
    `/api/projects/${projectId}/ai-usage/estimate?${q.toString()}`,
  );
}
