import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import type { GrowthAuditPageResult } from "@gcr/shared";
import { GrowthAuditProductIntelligenceSummary } from "../components/growth-audit/page-detail/GrowthAuditProductIntelligenceSummary";
import { GrowthAuditPriorityActionsPanel } from "../components/growth-audit/GrowthAuditPriorityActionsPanel";
import { GrowthAuditPageDetailShopifySection } from "../components/growth-audit/page-detail/GrowthAuditPageDetailShopifySection";
import { GrowthAuditPageDetailTechnicalSection } from "../components/growth-audit/page-detail/GrowthAuditPageDetailTechnicalSection";
import { GrowthAuditPageWorkspacePerformanceSection } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspacePerformanceSection";
import { GrowthAuditPageWorkspaceSearchConsoleSection } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspaceSearchConsoleSection";
import { GrowthAuditPageWorkspaceAnalyticsSection } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspaceAnalyticsSection";
import { GrowthAuditPageWorkspaceAiSection } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspaceAiSection";
import { GrowthAuditPageWorkspaceHeader } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspaceHeader";
import { GrowthAuditPageWorkspaceSidebar } from "../components/growth-audit/page-detail/GrowthAuditPageWorkspaceSidebar";
import {
  useGrowthAuditFindings,
  useGrowthAuditPageResults,
  useGrowthAuditRun,
  useGrowthAuditTasks,
  useRescanGrowthAuditPage,
} from "../hooks/useGrowthAudit";
import {
  buildGrowthAuditPageImprovementItems,
  buildGrowthAuditPriorityActions,
  getFindingsForPage,
  getTasksForPage,
  hasGrowthAuditPagePerformanceAnalysis,
  hasGrowthAuditPageAnalyticsData,
  hasGrowthAuditPageSearchConsoleData,
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
  const { data: performanceResults = [] } = useGrowthAuditPageResults(
    projectId,
    runId,
    pageId,
    { resultType: "performance" },
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
  const hasPerformanceResult = useMemo(
    () =>
      getLatestCompletedAiResult(performanceResults) != null ||
      (page ? hasGrowthAuditPagePerformanceAnalysis(page) : false),
    [performanceResults, page],
  );
  const hasSearchConsoleData = useMemo(
    () => (page ? hasGrowthAuditPageSearchConsoleData(page) : false),
    [page],
  );
  const hasAnalyticsData = useMemo(
    () => (page ? hasGrowthAuditPageAnalyticsData(page) : false),
    [page],
  );
  const mappedEntity = page ? mapGrowthAuditPageToSeoEntity(page) : null;
  const aiAvailable = page?.status === "analyzed";

  const priorityActions = useMemo(() => {
    if (!page) return [];
    return buildGrowthAuditPriorityActions({
      page,
      findings: pageFindings,
      tasks: pageTasks,
      improvementItems: buildGrowthAuditPageImprovementItems(page, pageFindings),
      aiResults: pageResults,
    });
  }, [page, pageFindings, pageTasks, pageResults]);

  const priorityActionsCount = priorityActions.length;

  const canRescan = Boolean(
    projectId &&
      runId &&
      page &&
      page.status !== "analyzing" &&
      !isGrowthAuditRunActive(runStatus),
  );

  if (!projectId || !runId || !pageId) {
    return (
      <div className="growth-audit-workspace growth-audit-page-detail">
        <p>Parametri mancanti per il dettaglio pagina.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="growth-audit-workspace growth-audit-page-detail">
        <p className="growth-audit-page-detail__loading">Caricamento pagina…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="growth-audit-workspace growth-audit-page-detail">
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
      <div className="growth-audit-workspace growth-audit-page-detail">
        <p className="growth-audit-page-detail__empty">Pagina non trovata in questo run.</p>
        <Link to={APP_ROUTES.projectGrowthAudit(projectId)} className="gcr-btn gcr-btn--secondary">
          ← Torna all&apos;audit
        </Link>
      </div>
    );
  }

  return (
    <div className="growth-audit-workspace growth-audit-page-detail">
      <GrowthAuditPageWorkspaceHeader
        projectId={projectId}
        page={page}
        runStatus={runStatus}
        findingsCount={pageFindings.length}
        tasksCount={pageTasks.length}
        latestAiResult={latestAiResult}
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

      <div className="growth-audit-workspace__layout">
        <main className="growth-audit-workspace__main">
          <GrowthAuditProductIntelligenceSummary
            page={page}
            findings={pageFindings}
            tasks={pageTasks}
            priorityActions={priorityActions}
            aiResults={pageResults}
            performanceResults={performanceResults}
          />

          <GrowthAuditPriorityActionsPanel
            page={page}
            findings={pageFindings}
            tasks={pageTasks}
            aiResults={pageResults}
            maxItems={6}
            workspace
          />

          <GrowthAuditPageDetailShopifySection projectId={projectId} page={page} />

          <GrowthAuditPageWorkspacePerformanceSection
            projectId={projectId}
            runId={runId}
            page={page}
            runStatus={runStatus}
          />

          <GrowthAuditPageWorkspaceSearchConsoleSection page={page} />

          <GrowthAuditPageWorkspaceAnalyticsSection page={page} />

          <GrowthAuditPageWorkspaceAiSection
            projectId={projectId}
            runId={runId}
            page={page}
            runStatus={runStatus}
            aiAvailable={Boolean(aiAvailable)}
          />

          <GrowthAuditPageDetailTechnicalSection page={page} />
        </main>

        <GrowthAuditPageWorkspaceSidebar
          page={page}
          priorityActionsCount={priorityActionsCount}
          openFindingsCount={pageFindings.length}
          openTasksCount={pageTasks.length}
          hasAiResult={Boolean(latestAiResult)}
          hasPerformanceResult={hasPerformanceResult}
          hasSearchConsoleData={hasSearchConsoleData}
          hasAnalyticsData={hasAnalyticsData}
          shopifySectionAvailable={Boolean(mappedEntity)}
          aiSectionAvailable={Boolean(aiAvailable)}
          onScrollToSection={scrollToSection}
        />
      </div>
    </div>
  );
}
