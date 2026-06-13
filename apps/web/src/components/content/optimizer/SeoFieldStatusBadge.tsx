import type { SeoScoreBreakdown } from "@gcr/shared";
import { getFieldStatus, type FieldStatus } from "./seoFormValues";

const LABELS: Record<FieldStatus, string> = {
  ok: "OK",
  missing: "Mancante",
  improve: "Da migliorare",
  verify: "Da verificare",
};

interface SeoFieldStatusBadgeProps {
  field: string;
  value: unknown;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  aiFilledFields?: Set<string>;
}

export function SeoFieldStatusBadge({
  field,
  value,
  issues,
  scoreBreakdown,
  aiFilledFields,
}: SeoFieldStatusBadgeProps) {
  const { status } = getFieldStatus(field, value, issues, scoreBreakdown, aiFilledFields);
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
  aiFilledFields?: Set<string>,
): string | undefined {
  const { note, status } = getFieldStatus(field, value, issues, scoreBreakdown, aiFilledFields);
  return status !== "ok" ? note : undefined;
}
