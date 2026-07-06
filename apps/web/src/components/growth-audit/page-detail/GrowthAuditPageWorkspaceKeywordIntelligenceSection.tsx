import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageKeywordIntelligencePanel } from "../GrowthAuditPageKeywordIntelligencePanel";
import { isGrowthAuditProductPage } from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceKeywordIntelligenceSectionProps {
  projectId: string;
  runId: string;
  page: GrowthAuditPage;
  runStatus?: string;
}

export function GrowthAuditPageWorkspaceKeywordIntelligenceSection({
  projectId,
  runId,
  page,
  runStatus,
}: GrowthAuditPageWorkspaceKeywordIntelligenceSectionProps) {
  if (!isGrowthAuditProductPage(page)) {
    return null;
  }

  return (
    <section
      id="keyword-intelligence"
      className="growth-audit-keyword-intelligence-workspace growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Keyword Intelligence</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Arricchisce le query Search Console con volumi, competitor SERP e idee keyword da
          DataForSEO.
        </p>
      </header>
      <GrowthAuditPageKeywordIntelligencePanel
        projectId={projectId}
        runId={runId}
        page={page}
        runStatus={runStatus}
      />
    </section>
  );
}
