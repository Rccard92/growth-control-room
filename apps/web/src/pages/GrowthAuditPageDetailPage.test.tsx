import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { GrowthAuditPageDetailPage } from "./GrowthAuditPageDetailPage";

const {
  useParamsMock,
  useGrowthAuditRunMock,
  useGrowthAuditFindingsMock,
  useGrowthAuditTasksMock,
  useGrowthAuditPageResultsMock,
  useRescanGrowthAuditPageMock,
  useAnalyzeGrowthAuditPageWithAiMock,
  useAnalyzeGrowthAuditPagePerformanceMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useGrowthAuditRunMock: vi.fn(),
  useGrowthAuditFindingsMock: vi.fn(),
  useGrowthAuditTasksMock: vi.fn(),
  useGrowthAuditPageResultsMock: vi.fn(),
  useRescanGrowthAuditPageMock: vi.fn(),
  useAnalyzeGrowthAuditPageWithAiMock: vi.fn(),
  useAnalyzeGrowthAuditPagePerformanceMock: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: useParamsMock,
  };
});

vi.mock("../hooks/useGrowthAudit", () => ({
  useGrowthAuditRun: useGrowthAuditRunMock,
  useGrowthAuditFindings: useGrowthAuditFindingsMock,
  useGrowthAuditTasks: useGrowthAuditTasksMock,
  useGrowthAuditPageResults: useGrowthAuditPageResultsMock,
  useRescanGrowthAuditPage: useRescanGrowthAuditPageMock,
  useAnalyzeGrowthAuditPageWithAi: useAnalyzeGrowthAuditPageWithAiMock,
  useAnalyzeGrowthAuditPagePerformance: useAnalyzeGrowthAuditPagePerformanceMock,
}));

vi.mock("../hooks/useContentSeo", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../hooks/useContentSeo")>();
  const idleQuery = {
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  };
  const idleMutation = {
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
  };
  return {
    ...actual,
    useProductSeoDetail: vi.fn(() => idleQuery),
    useCollectionSeoDetail: vi.fn(() => idleQuery),
    useProductsSeo: vi.fn(() => idleQuery),
    useCollectionsSeo: vi.fn(() => idleQuery),
    useSaveManualProposal: vi.fn(() => idleMutation),
    useApplyEntityFields: vi.fn(() => idleMutation),
    useSyncProductSeo: vi.fn(() => idleMutation),
    useSyncCollectionSeo: vi.fn(() => idleMutation),
    useSyncMetafieldDefinitions: vi.fn(() => idleMutation),
  };
});

vi.mock("../hooks/useSeoAiQueue", () => ({
  useSeoAiQueue: vi.fn(() => ({
    enqueue: vi.fn(),
    isRunning: false,
  })),
}));

const sampleProductPage = {
  id: "page-2",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  title: "Miele",
  httpStatus: 200,
  score: 72,
  analyzedAt: "2026-06-13T10:00:00Z",
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-shopify-1",
  sourceEntityTitle: "Miele Premium",
  sourceEntityHandle: "miele",
  metadata: {
    technical: {
      schemaTypes: ["Product"],
      imagesTotal: 3,
      imagesMissingAlt: 0,
    },
  },
};

function setupDetailMocks() {
  useParamsMock.mockReturnValue({
    id: "proj-1",
    runId: "run-1",
    pageId: "page-2",
  });

  useGrowthAuditRunMock.mockReturnValue({
    data: {
      run: {
        id: "run-1",
        projectId: "proj-1",
        status: "completed",
        rootUrl: "https://solmielato.it",
        normalizedDomain: "solmielato.it",
        auditMode: "full_site_mvp",
        provider: "openai",
        progressPercent: 100,
        pagesDiscovered: 1,
        pagesClassified: 1,
        pagesAnalyzed: 1,
        pagesFailed: 0,
      },
      pages: [sampleProductPage],
      events: [],
      findingsCount: 1,
      tasksCount: 1,
    },
    isLoading: false,
    isError: false,
  });

  useGrowthAuditFindingsMock.mockReturnValue({
    data: [
      {
        id: "finding-1",
        runId: "run-1",
        projectId: "proj-1",
        pageId: "page-2",
        category: "seo",
        severity: "high",
        priority: "high",
        title: "Title debole",
        description: "Il title non è ottimizzato.",
        recommendation: "Rafforza il title con keyword e brand.",
        howToValidate: "Verifica il tag title nel sorgente.",
        status: "open",
      },
    ],
  });

  useGrowthAuditTasksMock.mockReturnValue({
    data: [
      {
        id: "task-1",
        runId: "run-1",
        projectId: "proj-1",
        pageId: "page-2",
        title: "Ottimizza meta description",
        description: "Riscrivi la meta con benefit chiari.",
        ownerType: "seo",
        priority: "medium",
        estimatedEffort: "low",
        status: "open",
      },
    ],
  });

  useGrowthAuditPageResultsMock.mockImplementation(
    (_projectId, _runId, _pageId, filters?: { resultType?: string }) => ({
      data:
        filters?.resultType === "performance"
          ? [
              {
                id: "perf-result-1",
                runId: "run-1",
                projectId: "proj-1",
                pageId: "page-2",
                resultType: "performance",
                status: "completed",
                score: 68,
                summary: "Performance score 68.",
                artifacts: {
                  pagespeed: {
                    performanceScore: 68,
                    accessibilityScore: 90,
                    bestPracticesScore: 85,
                    seoLighthouseScore: 88,
                    lcp: 2800,
                    cls: 0.08,
                    tbt: 250,
                    fcp: 1200,
                  },
                  crux: { source: "missing" },
                  strategy: "mobile",
                },
              },
            ]
          : [],
      isLoading: false,
    }),
  );

  useRescanGrowthAuditPageMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });

  useAnalyzeGrowthAuditPageWithAiMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });

  useAnalyzeGrowthAuditPagePerformanceMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });
}

function renderDetailPage() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <GrowthAuditPageDetailPage />
    </MemoryRouter>,
  );
}

function indexOfOrFail(html: string, needle: string): number {
  const index = html.indexOf(needle);
  expect(index).toBeGreaterThanOrEqual(0);
  return index;
}

describe("GrowthAuditPageDetailPage", () => {
  it("renders workspace layout with sticky header", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("growth-audit-workspace");
    expect(html).toContain("growth-audit-workspace-header--sticky");
    expect(html).toContain("Torna al Growth Audit");
    expect(html).toContain("Prodotto");
    expect(html).toContain("Riscansiona pagina");
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("Analizza AI/GEO/CRO");
  });

  it("renders priority section before Shopify with workspace anchors", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    const priorityIndex = indexOfOrFail(html, 'id="priority-actions"');
    const shopifyIndex = indexOfOrFail(html, 'id="shopify-edit"');
    const performanceIndex = indexOfOrFail(html, 'id="performance"');
    const aiIndex = indexOfOrFail(html, 'id="ai-geo-cro"');
    expect(priorityIndex).toBeLessThan(shopifyIndex);
    expect(shopifyIndex).toBeLessThan(performanceIndex);
    expect(performanceIndex).toBeLessThan(aiIndex);
    expect(html).toContain("Cosa sistemare prima");
    expect(html).toContain("Dove intervenire");
    expect(html).toContain("Workflow consigliato");
  });

  it("renders performance section with CTA, scores and CrUX missing message", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("Performance / Core Web Vitals");
    expect(html).toContain("Analizza performance");
    expect(html).toContain("Performance Score");
    expect(html).toContain("CrUX non ha dati sufficienti per questa URL");
    expect(html).toContain("68");
  });

  it("renders Shopify callout and AI cost warning", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain(
      "Dopo aver salvato su Shopify, clicca Riscansiona pagina per aggiornare score e problemi.",
    );
    expect(html).toContain("genera una chiamata AI");
    expect(html).toContain("Analizza questa pagina");
  });

  it("renders collapsible technical data as secondary section", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain('id="technical-data"');
    expect(html).toContain("Dati tecnici");
    expect(html).toContain("Dettagli usati per calcolare lo score tecnico");
    expect(html).toContain("<details");
  });

  it("does not render duplicate main sections for improvements/problems/tasks", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).not.toContain("Come migliorare questa pagina");
    expect(html).not.toContain("Problemi prioritari");
    expect(html).not.toContain("growth-audit-tasks__title");
    expect(html).not.toContain("growth-audit-findings__title");
  });
});
