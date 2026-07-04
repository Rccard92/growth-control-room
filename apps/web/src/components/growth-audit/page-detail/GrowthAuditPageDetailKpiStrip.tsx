import type { GrowthAuditPage, GrowthAuditPageAiMetadata, GrowthAuditPageResult } from "@gcr/shared";
import {
  formatGrowthAuditScore,
  getGrowthAuditScoreBadgeClass,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageDetailKpiStripProps {
  page: GrowthAuditPage;
  openFindingsCount: number;
  openTasksCount: number;
  latestAiResult?: GrowthAuditPageResult | null;
}

function readAiMetadata(page: GrowthAuditPage): GrowthAuditPageAiMetadata | null {
  const ai = page.metadata?.ai;
  if (!ai || typeof ai !== "object") return null;
  return ai as GrowthAuditPageAiMetadata;
}

function formatKpiValue(value?: number | null): string {
  if (value == null) return "—";
  return String(value);
}

export function GrowthAuditPageDetailKpiStrip({
  page,
  openFindingsCount,
  openTasksCount,
  latestAiResult,
}: GrowthAuditPageDetailKpiStripProps) {
  const aiMeta = readAiMetadata(page);
  const rawOutput = latestAiResult?.rawOutput as Record<string, unknown> | undefined;

  const items = [
    { label: "Score tecnico", value: page.score, isScore: true },
    {
      label: "Score AI",
      value: latestAiResult?.score ?? aiMeta?.latestScore ?? null,
      isScore: true,
    },
    {
      label: "SEO",
      value: (rawOutput?.seoScore as number | undefined) ?? aiMeta?.seoScore ?? null,
      isScore: true,
    },
    {
      label: "GEO",
      value:
        (rawOutput?.geoScore as number | undefined) ?? page.geoScore ?? aiMeta?.geoScore ?? null,
      isScore: true,
    },
    {
      label: "CRO",
      value:
        (rawOutput?.croScore as number | undefined) ?? page.croScore ?? aiMeta?.croScore ?? null,
      isScore: true,
    },
    {
      label: "Ads readiness",
      value:
        (rawOutput?.adsReadinessScore as number | undefined) ??
        aiMeta?.adsReadinessScore ??
        null,
      isScore: true,
    },
    { label: "Problemi aperti", value: openFindingsCount, isScore: false },
    { label: "Task aperti", value: openTasksCount, isScore: false },
  ];

  return (
    <div className="growth-audit-page-detail__score-grid">
      {items.map((item) => (
        <div key={item.label} className="growth-audit-page-detail__kpi gcr-card">
          {item.isScore ? (
            <span className={getGrowthAuditScoreBadgeClass(item.value)}>
              {formatGrowthAuditScore(item.value)}
            </span>
          ) : (
            <span className="growth-audit-page-detail__kpi-value">
              {formatKpiValue(item.value)}
            </span>
          )}
          <span className="growth-audit-page-detail__kpi-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
