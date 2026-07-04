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
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useGrowthAuditRunMock: vi.fn(),
  useGrowthAuditFindingsMock: vi.fn(),
  useGrowthAuditTasksMock: vi.fn(),
  useGrowthAuditPageResultsMock: vi.fn(),
  useRescanGrowthAuditPageMock: vi.fn(),
  useAnalyzeGrowthAuditPageWithAiMock: vi.fn(),
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

  useGrowthAuditPageResultsMock.mockReturnValue({
    data: [],
    isLoading: false,
  });

  useRescanGrowthAuditPageMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });

  useAnalyzeGrowthAuditPageWithAiMock.mockReturnValue({
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

describe("GrowthAuditPageDetailPage", () => {
  it("renders page detail workspace with priority section", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("Dettaglio pagina");
    expect(html).toContain("Cosa sistemare prima");
    expect(html).toContain("Torna all");
    expect(html).toContain("Prodotto");
    expect(html).toContain("https://solmielato.it/products/miele");
  });

  it("renders Modifica Shopify section for shopify_product", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("riscansiona la pagina");
  });

  it("renders AI/GEO/CRO section", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("AI/GEO/CRO");
    expect(html).toContain("pagine prioritarie");
    expect(html).toContain("Analizza questa pagina");
  });

  it("renders collapsible technical data section", () => {
    setupDetailMocks();
    const html = renderDetailPage();
    expect(html).toContain("Mostra dati tecnici");
    expect(html).toContain("<details");
  });
});
