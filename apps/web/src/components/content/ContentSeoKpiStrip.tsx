import type { ContentSeoDashboardSummary } from "@gcr/shared";

interface ContentSeoKpiStripProps {
  summary: ContentSeoDashboardSummary;
}

const KPI_ITEMS: Array<{
  key: keyof ContentSeoDashboardSummary;
  label: string;
  accent?: string;
}> = [
  { key: "totalIssues", label: "Issues totali" },
  { key: "criticalIssues", label: "Criticità", accent: "rose" },
  { key: "contentOpportunities", label: "Opportunità contenuto", accent: "emerald" },
  { key: "productsWithoutMeta", label: "Prodotti senza meta" },
  { key: "collectionsWeak", label: "Collections deboli" },
];

export function ContentSeoKpiStrip({ summary }: ContentSeoKpiStripProps) {
  return (
    <div className="content-seo-kpi-strip">
      {KPI_ITEMS.map((item) => (
        <div key={item.key} className={`content-seo-kpi gcr-card ${item.accent ? `content-seo-kpi--${item.accent}` : ""}`}>
          <span className="content-seo-kpi__value">{summary[item.key] ?? 0}</span>
          <span className="content-seo-kpi__label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
