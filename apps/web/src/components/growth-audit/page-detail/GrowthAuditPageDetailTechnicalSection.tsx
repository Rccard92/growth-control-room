import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageTechnicalSummary } from "../GrowthAuditPageTechnicalSummary";

interface GrowthAuditPageDetailTechnicalSectionProps {
  page: GrowthAuditPage;
}

export function GrowthAuditPageDetailTechnicalSection({
  page,
}: GrowthAuditPageDetailTechnicalSectionProps) {
  return (
    <section
      id="section-technical"
      className="growth-audit-page-detail__section growth-audit-page-detail__technical-details"
    >
      <details className="growth-audit-page-detail__technical-collapsible">
        <summary>Mostra dati tecnici</summary>
        <GrowthAuditPageTechnicalSummary page={page} />
      </details>
    </section>
  );
}
