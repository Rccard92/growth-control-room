import type { SeoScoreBreakdown } from "@gcr/shared";
import { getFieldStatus, type FieldStatus } from "./seoFormValues";
import type { FieldState } from "./seoFieldState";

const LABELS: Record<FieldStatus, string> = {
  ok: "OK",
  missing: "Mancante",
  improve: "Da migliorare",
  verify: "Da verificare",
  ai_proposed: "Proposto da AI",
  accepted: "Accettato",
  generating: "AI…",
};

interface SeoFieldStatusBadgeProps {
  field: string;
  value: unknown;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  aiFilledFields?: Set<string>;
  fieldState?: FieldState;
}

export function SeoFieldStatusBadge({
  field,
  value,
  issues,
  scoreBreakdown,
  aiFilledFields,
  fieldState,
}: SeoFieldStatusBadgeProps) {
  const { status } = getFieldStatus(
    field,
    value,
    issues,
    scoreBreakdown,
    aiFilledFields,
    fieldState,
  );
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
  fieldState?: FieldState,
): string | undefined {
  const { note, status } = getFieldStatus(
    field,
    value,
    issues,
    scoreBreakdown,
    aiFilledFields,
    fieldState,
  );
  return status !== "ok" ? note : undefined;
}
