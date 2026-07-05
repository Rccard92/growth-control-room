import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPagePerformanceAnalysisPanel } from "../GrowthAuditPagePerformanceAnalysisPanel";

interface GrowthAuditPageWorkspacePerformanceSectionProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
}

export function GrowthAuditPageWorkspacePerformanceSection({
  projectId,
  runId,
  page,
  runStatus,
}: GrowthAuditPageWorkspacePerformanceSectionProps) {
  return (
    <section
      id="performance"
      className="growth-audit-performance-workspace growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Performance / Core Web Vitals</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Analizza velocità, Lighthouse e dati real-user CrUX quando disponibili.
        </p>
        <p className="growth-audit-performance-workspace__warning">
          Usa questa analisi sulle pagine prioritarie. PageSpeed può richiedere diversi secondi.
        </p>
      </header>

      <GrowthAuditPagePerformanceAnalysisPanel
        projectId={projectId}
        runId={runId}
        page={page}
        runStatus={runStatus}
      />
    </section>
  );
}
