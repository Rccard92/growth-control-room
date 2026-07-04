import type { GrowthAuditPage } from "@gcr/shared";
import {
  getGrowthAuditPageTechnicalMetadata,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageTechnicalSummaryProps {
  page: GrowthAuditPage;
}

function displayValue(value?: string | number | null): string {
  if (value == null || value === "") return "Non disponibile";
  return String(value);
}

function formatRobots(robots: { noindex?: boolean; nofollow?: boolean; raw?: string } | null): string {
  if (!robots) return "Non disponibile";
  const parts: string[] = [];
  if (robots.noindex) parts.push("noindex");
  if (robots.nofollow) parts.push("nofollow");
  if (parts.length > 0) return parts.join(", ");
  if (robots.raw) return robots.raw;
  return "Nessuna restrizione";
}

export function GrowthAuditPageTechnicalSummary({ page }: GrowthAuditPageTechnicalSummaryProps) {
  const technical = getGrowthAuditPageTechnicalMetadata(page);
  const schemaLabel =
    technical.schemaTypes.length > 0 ? technical.schemaTypes.join(", ") : "Nessuno";

  const items = [
    { label: "HTTP status", value: displayValue(page.httpStatus) },
    { label: "Title", value: displayValue(page.title) },
    { label: "Meta description", value: displayValue(page.metaDescription) },
    { label: "H1", value: displayValue(page.h1) },
    { label: "Canonical", value: displayValue(page.canonicalUrl) },
    { label: "Schema types", value: schemaLabel },
    {
      label: "Immagini totali",
      value: displayValue(technical.imagesTotal),
    },
    {
      label: "Immagini senza alt",
      value: displayValue(technical.imagesMissingAlt),
    },
    {
      label: "Link interni",
      value: displayValue(technical.linksInternal),
    },
    {
      label: "Link esterni",
      value: displayValue(technical.linksExternal),
    },
    { label: "Robots", value: formatRobots(technical.robots) },
  ];

  return (
    <section className="growth-audit-page-drawer__section">
      <h4 className="growth-audit-page-drawer__section-title">Dati tecnici</h4>
      <div className="growth-audit-page-tech-grid">
        {items.map((item) => (
          <div key={item.label} className="growth-audit-page-tech-card">
            <span className="growth-audit-page-tech-card__label">{item.label}</span>
            <span className="growth-audit-page-tech-card__value">{item.value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
