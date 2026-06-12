import type { SeoOptimizerSeverity } from "@gcr/shared";

const SEVERITY_CLASS: Record<string, string> = {
  critical: "seo-score--critical",
  warning: "seo-score--warning",
  opportunity: "seo-score--opportunity",
  good: "seo-score--good",
};

interface SeoScoreBadgeProps {
  score: number | null | undefined;
  severity?: SeoOptimizerSeverity | null;
}

export function SeoScoreBadge({ score, severity }: SeoScoreBadgeProps) {
  if (score == null) {
    return <span className="seo-score seo-score--na">—</span>;
  }
  const cls = severity ? SEVERITY_CLASS[severity] ?? "" : "";
  return <span className={`seo-score ${cls}`}>{score}</span>;
}
