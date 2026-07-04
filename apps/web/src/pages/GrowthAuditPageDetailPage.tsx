import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import type { GrowthAuditPageResult } from "@gcr/shared";
import { GrowthAuditPageAiAnalysisPanel } from "../components/growth-audit/GrowthAuditPageAiAnalysisPanel";
import { GrowthAuditPageDetailHeader } from "../components/growth-audit/page-detail/GrowthAuditPageDetailHeader";
import { GrowthAuditPageDetailKpiStrip } from "../components/growth-audit/page-detail/GrowthAuditPageDetailKpiStrip";
import { GrowthAuditPageDetailShopifySection } from "../components/growth-audit/page-detail/GrowthAuditPageDetailShopifySection";
import { GrowthAuditPageDetailSidebar } from "../components/growth-audit/page-detail/GrowthAuditPageDetailSidebar";
import { GrowthAuditPageDetailTechnicalSection } from "../components/growth-audit/page-detail/GrowthAuditPageDetailTechnicalSection";
import { GrowthAuditPriorityActionsPanel } from "../components/growth-audit/GrowthAuditPriorityActionsPanel";
import {
  useGrowthAuditFindings,
  useGrowthAuditPageResults,
  useGrowthAuditRun,
  useGrowthAuditTasks,
  useRescanGrowthAuditPage,
} from "../hooks/useGrowthAudit";
import {
  getFindingsForPage,
  getTasksForPage,
  isGrowthAuditRunActive,
  mapGrowthAuditPageToSeoEntity,
  sortGrowthAuditFindings,
  sortGrowthAuditTasks,
} from "../lib/growth-audit-utils";
import { APP_ROUTES } from "../routes/config";

function scrollToSection(sectionId: string) {
  document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function getLatestCompletedAiResult(
  results: GrowthAuditPageResult[] | undefined,
): GrowthAuditPageResult | null {
  const completed = (results ?? []).filter((result) => result.status === "completed");
  if (completed.length === 0) return null;
  return completed.sort((a, b) => {
    const aTime = a.completedAt ?? a.createdAt ?? "";
    const bTime = b.completedAt ?? b.createdAt ?? "";
    return bTime.localeCompare(aTime);
  })[0];
}

export function GrowthAuditPageDetailPage() {
  const { id, runId, pageId } = useParams<{ id: string; runId: string; pageId: string }>();
  const projectId = id ?? "";

  const { data: runDetail, isLoading, isError, error } = useGrowthAuditRun(
    projectId,
    runId,
    Boolean(projectId && runId),
  );
  const runStatus = runDetail?.run.status;
  const { data: findings = [] } = useGrowthAuditFindings(
    projectId,
    runId,
    undefined,
    runStatus,
    Boolean(projectId && runId),
  );
  const { data: tasks = [] } = useGrowthAuditTasks(
    projectId,
    runId,
    { status: "open" },
    runStatus,
    Boolean(projectId && runId),
  );
  const { data: pageResults = [] } = useGrowthAuditPageResults(
    projectId,
    runId,
    pageId,
    { resultType: "ai_deep_analysis" },
    Boolean(projectId && runId && pageId),
  );
  const rescanPage = useRescanGrowthAuditPage(projectId);

  const page = useMemo(
    () => runDetail?.pages.find((item) => item.id === pageId) ?? null,
    [runDetail?.pages, pageId],
  );
  const pageFindings = useMemo(
    () => sortGrowthAuditFindings(getFindingsForPage(findings, pageId ?? null)),
    [findings, pageId],
  );
  const pageTasks = useMemo(
    () => sortGrowthAuditTasks(getTasksForPage(tasks, pageId ?? null)),
    [tasks, pageId],
  );
  const latestAiResult = useMemo(() => getLatestCompletedAiResult(pageResults), [pageResults]);
  const mappedEntity = page ? mapGrowthAuditPageToSeoEntity(page) : null;
  const aiAvailable = page?.status === "analyzed";

  const canRescan = Boolean(
    projectId &&
      runId &&
      page &&
      page.status !== "analyzing" &&
      !isGrowthAuditRunActive(runStatus),
  );

  if (!projectId || !runId || !pageId) {
    return (
      <div className="growth-audit-page-detail">
        <p>Parametri mancanti per il dettaglio pagina.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="growth-audit-page-detail">
        <p className="growth-audit-page-detail__loading">Caricamento pagina…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="growth-audit-page-detail">
        <div className="gcr-alert gcr-alert--error" role="alert">
          {error instanceof Error ? error.message : "Impossibile caricare il dettaglio pagina."}
        </div>
        <Link to={APP_ROUTES.projectGrowthAudit(projectId)} className="gcr-btn gcr-btn--secondary">
          ← Torna all&apos;audit
        </Link>
      </div>
    );
  }

  if (!page) {
    return (
      <div className="growth-audit-page-detail">
        <p className="growth-audit-page-detail__empty">Pagina non trovata in questo run.</p>
        <Link to={APP_ROUTES.projectGrowthAudit(projectId)} className="gcr-btn gcr-btn--secondary">
          ← Torna all&apos;audit
        </Link>
      </div>
    );
  }

  return (
    <div className="growth-audit-page-detail">
      <GrowthAuditPageDetailHeader
        projectId={projectId}
        page={page}
        runStatus={runStatus}
        isRescanning={rescanPage.isPending}
        canRescan={canRescan}
        onRescan={async (clearPreviousOpenItems) => {
          await rescanPage.mutateAsync({
            runId: runId!,
            pageId: page.id,
            payload: { clearPreviousOpenItems },
          });
        }}
        onScrollToSection={scrollToSection}
      />

      <GrowthAuditPageDetailKpiStrip
        page={page}
        openFindingsCount={pageFindings.length}
        openTasksCount={pageTasks.length}
        latestAiResult={latestAiResult}
      />

      <div className="growth-audit-page-detail__layout">
        <main className="growth-audit-page-detail__main">
          <GrowthAuditPriorityActionsPanel
            page={page}
            findings={pageFindings}
            tasks={pageTasks}
            aiResults={pageResults}
          />

          <GrowthAuditPageDetailShopifySection projectId={projectId} page={page} />

          <section
            id="section-ai"
            className="growth-audit-page-detail__section growth-audit-page-detail__ai"
          >
            <h2 className="growth-audit-page-detail__section-title">AI/GEO/CRO</h2>
            <p className="growth-audit-page-detail__ai-intro">
              Usa questa analisi solo sulle pagine prioritarie. L&apos;analisi usa AI e può
              generare costi.
            </p>
            {aiAvailable ? (
              <GrowthAuditPageAiAnalysisPanel
                projectId={projectId}
                runId={runId}
                page={page}
                runStatus={runStatus}
              />
            ) : (
              <p className="growth-audit-page-detail__empty">
                Completa prima la scansione tecnica della pagina per abilitare l&apos;analisi
                AI/GEO/CRO.
              </p>
            )}
          </section>

          <GrowthAuditPageDetailTechnicalSection page={page} />
        </main>

        <GrowthAuditPageDetailSidebar
          page={page}
          onScrollToSection={scrollToSection}
          shopifySectionAvailable={Boolean(mappedEntity)}
          aiSectionAvailable={Boolean(aiAvailable)}
        />
      </div>
    </div>
  );
}
