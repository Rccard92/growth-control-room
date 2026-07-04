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
      id="technical-data"
      className="growth-audit-technical-collapsible growth-audit-workspace-section"
    >
      <details className="growth-audit-technical-collapsible__details">
        <summary className="growth-audit-technical-collapsible__summary">Dati tecnici</summary>
        <p className="growth-audit-technical-collapsible__description">
          Dettagli usati per calcolare lo score tecnico. Utili per debug e verifica.
        </p>
        <GrowthAuditPageTechnicalSummary page={page} />
      </details>
    </section>
  );
}
