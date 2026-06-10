import {
  DATE_RANGE_OPTIONS,
  DEFAULT_DATE_RANGE,
  type DateRangeParams,
  type DateRangePreset,
} from "@gcr/shared";

const VALID_PRESETS = new Set<DateRangePreset>(
  DATE_RANGE_OPTIONS.map((option) => option.value),
);

export function isValidDateRangePreset(value: string | null): value is DateRangePreset {
  return value != null && VALID_PRESETS.has(value as DateRangePreset);
}

export function parseDateRangeFromSearchParams(
  searchParams: URLSearchParams,
): DateRangeParams {
  const rangeParam = searchParams.get("range");
  const range = isValidDateRangePreset(rangeParam) ? rangeParam : DEFAULT_DATE_RANGE;
  const startDate = searchParams.get("start_date") ?? undefined;
  const endDate = searchParams.get("end_date") ?? undefined;

  if (range === "custom" && startDate && endDate) {
    return { range, startDate, endDate };
  }

  if (range === "custom") {
    return { range: DEFAULT_DATE_RANGE };
  }

  return { range };
}

export function dateRangeToQueryParams(params: DateRangeParams): URLSearchParams {
  const query = new URLSearchParams();
  query.set("range", params.range);

  if (params.range === "custom" && params.startDate && params.endDate) {
    query.set("start_date", params.startDate);
    query.set("end_date", params.endDate);
  }

  return query;
}

export function dateRangeToApiQueryString(params: DateRangeParams): string {
  return dateRangeToQueryParams(params).toString();
}

export function mergeDateRangeSearchParams(
  current: URLSearchParams,
  dateRange: DateRangeParams,
): URLSearchParams {
  const next = new URLSearchParams(current);
  next.set("range", dateRange.range);

  if (dateRange.range === "custom" && dateRange.startDate && dateRange.endDate) {
    next.set("start_date", dateRange.startDate);
    next.set("end_date", dateRange.endDate);
  } else {
    next.delete("start_date");
    next.delete("end_date");
  }

  return next;
}

export function getDateRangeDisplayLabel(
  params: DateRangeParams,
  apiLabel?: string,
): string {
  if (apiLabel) return apiLabel;
  if (params.range === "custom" && params.startDate && params.endDate) {
    return `Personalizzato: ${params.startDate} – ${params.endDate}`;
  }
  return DATE_RANGE_OPTIONS.find((option) => option.value === params.range)?.label ?? params.range;
}
