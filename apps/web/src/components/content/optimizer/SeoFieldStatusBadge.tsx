import type { SeoScoreBreakdown } from "@gcr/shared";
import { getFieldStatus, type FieldStatus } from "./seoFormValues";

const LABELS: Record<FieldStatus, string> = {
  ok: "OK",
  missing: "Mancante",
  improve: "Da migliorare",
};

interface SeoFieldStatusBadgeProps {
  field: string;
  value: unknown;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
}

export function SeoFieldStatusBadge({
  field,
  value,
  issues,
  scoreBreakdown,
}: SeoFieldStatusBadgeProps) {
  const { status } = getFieldStatus(field, value, issues, scoreBreakdown);
  return (
    <span className={`seo-field-status-badge seo-field-status-badge--${status}`}>
      {LABELS[status]}
    </span>
  );
}

export function fieldStatusNote(
  field: string,
  value: unknown,
  issues?: Record<string, unknown>[] | null,
  scoreBreakdown?: SeoScoreBreakdown | null,
): string | undefined {
  const { note, status } = getFieldStatus(field, value, issues, scoreBreakdown);
  return status !== "ok" ? note : undefined;
}
