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
  local_draft: "Bozza locale",
  apply_failed: "Errore apply",
};

interface SeoFieldStatusBadgeProps {
  field: string;
  value: unknown;
  issues?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  aiFilledFields?: Set<string>;
  fieldState?: FieldState;
  shopifyApplicable?: boolean;
  perImageMode?: boolean;
  applicabilityNote?: string;
}

export function SeoFieldStatusBadge({
  field,
  value,
  issues,
  scoreBreakdown,
  aiFilledFields,
  fieldState,
  shopifyApplicable,
  perImageMode,
  applicabilityNote,
}: SeoFieldStatusBadgeProps) {
  const { status } = getFieldStatus(
    field,
    value,
    issues,
    scoreBreakdown,
    aiFilledFields,
    fieldState,
    { shopifyApplicable, perImageMode, applicabilityNote },
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
  options?: {
    shopifyApplicable?: boolean;
    perImageMode?: boolean;
    applicabilityNote?: string;
  },
): string | undefined {
  const { note, status } = getFieldStatus(
    field,
    value,
    issues,
    scoreBreakdown,
    aiFilledFields,
    fieldState,
    options,
  );
  return status !== "ok" ? note : undefined;
}
