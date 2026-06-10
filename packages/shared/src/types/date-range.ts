export type DateRangePreset =
  | "today"
  | "yesterday"
  | "last_7_days"
  | "last_30_days"
  | "month_to_date"
  | "previous_month"
  | "custom";

export interface DateRangeParams {
  range: DateRangePreset;
  startDate?: string;
  endDate?: string;
}

export interface DateRangeOption {
  value: DateRangePreset;
  label: string;
}

export const DEFAULT_DATE_RANGE: DateRangePreset = "last_30_days";

export const DATE_RANGE_OPTIONS: DateRangeOption[] = [
  { value: "today", label: "Oggi" },
  { value: "yesterday", label: "Ieri" },
  { value: "last_7_days", label: "Ultimi 7 giorni" },
  { value: "last_30_days", label: "Ultimi 30 giorni" },
  { value: "month_to_date", label: "Mese corrente" },
  { value: "previous_month", label: "Mese precedente" },
  { value: "custom", label: "Personalizzato" },
];

export function getDateRangeLabel(preset: DateRangePreset): string {
  return DATE_RANGE_OPTIONS.find((option) => option.value === preset)?.label ?? preset;
}
