import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageAiAnalysisPanel } from "../GrowthAuditPageAiAnalysisPanel";

interface GrowthAuditPageWorkspaceAiSectionProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
  aiAvailable: boolean;
}

export function GrowthAuditPageWorkspaceAiSection({
  projectId,
  runId,
  page,
  runStatus,
  aiAvailable,
}: GrowthAuditPageWorkspaceAiSectionProps) {
  return (
    <section
      id="ai-geo-cro"
      className="growth-audit-ai-workspace growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">AI/GEO/CRO</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Analisi avanzata per contenuto, citabilità AI, persuasione, CRO e readiness per ads.
        </p>
        <p className="growth-audit-ai-workspace__warning">
          Usala sulle pagine prioritarie: genera una chiamata AI.
        </p>
      </header>

      {aiAvailable ? (
        <GrowthAuditPageAiAnalysisPanel
          projectId={projectId}
          runId={runId}
          page={page}
          runStatus={runStatus}
        />
      ) : (
        <p className="growth-audit-ai-workspace__empty">
          Completa prima la scansione tecnica della pagina per abilitare l&apos;analisi AI/GEO/CRO.
        </p>
      )}
    </section>
  );
}
