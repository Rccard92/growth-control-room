import type { GrowthAuditFinding } from "@gcr/shared";
import {
  getGrowthAuditFindingSeverityLabel,
  getGrowthAuditSeverityBadgeClass,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageFindingsPanelProps {
  findings: GrowthAuditFinding[];
}

function FindingField({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="growth-audit-page-finding__field">
      <span className="growth-audit-page-finding__field-label">{label}</span>
      <p>{value}</p>
    </div>
  );
}

export function GrowthAuditPageFindingsPanel({ findings }: GrowthAuditPageFindingsPanelProps) {
  return (
    <section className="growth-audit-page-drawer__section">
      <h4 className="growth-audit-page-drawer__section-title">Problemi</h4>
      {findings.length === 0 ? (
        <p className="growth-audit-page-drawer__empty">
          Nessun problema tecnico prioritario rilevato per questa pagina.
        </p>
      ) : (
        <ul className="growth-audit-page-findings">
          {findings.map((finding) => (
            <li
              key={finding.id}
              className={`growth-audit-page-finding growth-audit-page-finding--${finding.severity}`}
            >
              <div className="growth-audit-page-finding__header">
                <span className={getGrowthAuditSeverityBadgeClass(finding.severity)}>
                  {getGrowthAuditFindingSeverityLabel(finding.severity)}
                </span>
                <span className="growth-audit-page-finding__category">{finding.category}</span>
              </div>
              <strong className="growth-audit-page-finding__title">{finding.title}</strong>
              <FindingField label="Cosa succede" value={finding.description} />
              <FindingField label="Evidenza" value={finding.evidence} />
              {finding.recommendation && (
                <div className="growth-audit-page-finding__field growth-audit-page-finding__recommendation">
                  <span className="growth-audit-page-finding__field-label">Come risolvere</span>
                  <p>{finding.recommendation}</p>
                </div>
              )}
              <FindingField label="Come verificare" value={finding.howToValidate} />
              {(finding.impact || finding.effort) && (
                <div className="growth-audit-page-finding__meta">
                  {finding.impact && <span>Impatto: {finding.impact}</span>}
                  {finding.effort && <span>Sforzo: {finding.effort}</span>}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
