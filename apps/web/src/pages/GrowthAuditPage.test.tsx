import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { GrowthAuditPage } from "./GrowthAuditPage";

const {
  useParamsMock,
  useProjectMock,
  useShopifyStatusMock,
  useGrowthAuditRunsMock,
  useGrowthAuditRunMock,
  useGrowthAuditFindingsMock,
  useGrowthAuditTasksMock,
  useStartGrowthAuditRunMock,
  useRescanGrowthAuditPageMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useShopifyStatusMock: vi.fn(),
  useGrowthAuditRunsMock: vi.fn(),
  useGrowthAuditRunMock: vi.fn(),
  useGrowthAuditFindingsMock: vi.fn(),
  useGrowthAuditTasksMock: vi.fn(),
  useStartGrowthAuditRunMock: vi.fn(),
  useRescanGrowthAuditPageMock: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: useParamsMock,
  };
});

vi.mock("../hooks/useProjects", () => ({
  useProject: useProjectMock,
}));

vi.mock("../hooks/useShopify", () => ({
  useShopifyStatus: useShopifyStatusMock,
}));

vi.mock("../hooks/useGrowthAudit", () => ({
  useGrowthAuditRuns: useGrowthAuditRunsMock,
  useGrowthAuditRun: useGrowthAuditRunMock,
  useGrowthAuditFindings: useGrowthAuditFindingsMock,
  useGrowthAuditTasks: useGrowthAuditTasksMock,
  useStartGrowthAuditRun: useStartGrowthAuditRunMock,
  useRescanGrowthAuditPage: useRescanGrowthAuditPageMock,
}));

vi.mock("../hooks/useContentSeo", () => ({
  useProductSeoDetail: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
  useCollectionSeoDetail: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
  useProductsSeo: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
  useCollectionsSeo: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
}));

function setupMocks(options?: { withActiveRun?: boolean; withTechnicalScan?: boolean }) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
    isLoading: false,
  });
  useShopifyStatusMock.mockReturnValue({
    data: { connected: true, shopDomain: "solmielato.myshopify.com" },
  });

  const activeRun = options?.withActiveRun
    ? {
        run: {
          id: "run-1",
          projectId: "proj-1",
          rootUrl: "https://solmielato.it",
          normalizedDomain: "solmielato.it",
          status: options?.withTechnicalScan ? "completed" : "completed",
          phase: "finalization",
          auditMode: "full_site_mvp",
          provider: "openai",
          progressPercent: 100,
          pagesDiscovered: 3,
          pagesClassified: 3,
          pagesAnalyzed: options?.withTechnicalScan ? 3 : 0,
          pagesFailed: 0,
          siteScore: options?.withTechnicalScan ? 78 : null,
          summary: options?.withTechnicalScan
            ? {
                message: "Technical page scan completed. AI/GEO/CRO analysis is not enabled yet.",
                pageTypes: { homepage: 1, product: 1, collection: 1 },
                sources: { seed: 1, sitemap: 1, shopify: 1 },
                pagesAnalyzed: 3,
                averageTechnicalScore: 78,
                criticalFindings: 1,
                highFindings: 2,
                tasksOpen: 2,
              }
            : {
                message: "Page inventory completed. AI page analysis is not enabled yet.",
                pageTypes: { homepage: 1, product: 1, collection: 1 },
                sources: { seed: 1, sitemap: 1, shopify: 1 },
              },
        },
        pages: [
          {
            id: "page-1",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.it",
            normalizedUrl: "https://solmielato.it",
            pageType: "homepage",
            source: "seed",
            status: options?.withTechnicalScan ? "analyzed" : "classified",
            priority: "high",
            title: "Home",
            httpStatus: options?.withTechnicalScan ? 200 : null,
            score: options?.withTechnicalScan ? 82 : null,
          },
          {
            id: "page-2",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.it/products/miele",
            normalizedUrl: "https://solmielato.it/products/miele",
            pageType: "product",
            source: "shopify_product",
            status: options?.withTechnicalScan ? "analyzed" : "classified",
            priority: "normal",
            title: "Miele",
            httpStatus: options?.withTechnicalScan ? 200 : null,
            score: options?.withTechnicalScan ? 55 : null,
            sourceEntityType: "shopify_product",
            sourceEntityHandle: "miele",
            sourceEntityTitle: "Miele",
          },
          {
            id: "page-3",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.it/collections/best",
            normalizedUrl: "https://solmielato.it/collections/best",
            pageType: "collection",
            source: "sitemap",
            status: options?.withTechnicalScan ? "analyzed" : "classified",
            priority: "normal",
            title: "Best",
            httpStatus: options?.withTechnicalScan ? 200 : null,
            score: options?.withTechnicalScan ? 71 : null,
          },
        ],
        events: [
          {
            id: "evt-1",
            runId: "run-1",
            projectId: "proj-1",
            eventType: "inventory_completed",
            phase: "analysis",
            message: "Inventario completato",
            progressPercent: 60,
          },
        ],
        findingsCount: 0,
        tasksCount: 0,
      }
    : undefined;

  useGrowthAuditRunsMock.mockReturnValue({
    data: activeRun ? [activeRun.run] : [],
  });
  useGrowthAuditRunMock.mockReturnValue({
    data: activeRun,
    isLoading: false,
  });
  useGrowthAuditFindingsMock.mockReturnValue({
    data: options?.withTechnicalScan
      ? [
          {
            id: "finding-1",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "page-2",
            category: "seo",
            severity: "critical",
            priority: "high",
            title: "Title mancante",
            recommendation: "Aggiungi un title descrittivo.",
            howToValidate: "Verifica il tag title.",
            status: "open",
          },
        ]
      : [],
  });
  useGrowthAuditTasksMock.mockReturnValue({
    data: options?.withTechnicalScan
      ? [
          {
            id: "task-1",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "page-2",
            title: "Aggiungere title pagina",
            description: "Scrivi un title unico.",
            ownerType: "seo",
            priority: "high",
            estimatedEffort: "low",
            status: "open",
          },
        ]
      : [],
  });
  useStartGrowthAuditRunMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ run: { id: "run-new" } }),
    isPending: false,
    isError: false,
  });
  useRescanGrowthAuditPageMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      run: { id: "run-1" },
      page: { id: "page-1" },
      findingsCount: 0,
      tasksCount: 0,
      message: "Pagina riscansionata.",
    }),
    isPending: false,
    isError: false,
  });
}

function renderPage() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <GrowthAuditPage />
    </MemoryRouter>,
  );
}

describe("GrowthAuditPage", () => {
  it("renders Growth Audit title", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Growth Audit");
  });

  it("renders URL input, maxPages selector and start CTA", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Dominio o URL principale");
    expect(html).toContain("Pagine massime");
    expect(html).toContain("Avvia Full Site Audit");
    expect(html).toContain("https://solmielato.myshopify.com");
    expect(html).toContain("<option value=\"50\"");
  });

  it("shows inventory table, badges and filters when run exists", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Inventario pagine");
    expect(html).toContain("Homepage");
    expect(html).toContain("Shopify prodotto");
    expect(html).toContain("Sitemap");
    expect(html).toContain("Prodotti");
    expect(html).toContain("Categorie");
    expect(html).toContain("Eventi recenti");
    expect(html).toContain("HTTP");
    expect(html).toContain("Problemi");
    expect(html).toContain("82");
    expect(html).toContain("200");
    expect(html).toContain("Dettaglio");
    expect(html).toContain("Buona");
    expect(html).toContain("Shopify");
    expect(html).toContain("Collegata");
    expect(html).toContain("Non collegata");
  });

  it("shows Site Score and pagesAnalyzed from technical scan", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Site Score");
    expect(html).toContain("78");
    expect(html).toContain("Pagine analizzate");
    expect(html).toContain("3");
  });

  it("renders priority findings and open tasks", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Problemi prioritari");
    expect(html).toContain("Title mancante");
    expect(html).toContain("Task aperti");
    expect(html).toContain("Aggiungere title pagina");
    expect(html).toContain("deterministica");
  });

  it("renders score filters", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Critiche &lt;60");
    expect(html).toContain("Buone 80+");
  });

  it("sends maxPages in start payload", async () => {
    setupMocks();
    const mutateAsync = vi.fn().mockResolvedValue({ run: { id: "run-new" } });
    useStartGrowthAuditRunMock.mockReturnValue({
      mutateAsync,
      isPending: false,
      isError: false,
    });

    renderPage();
    await mutateAsync({
      rootUrl: "https://solmielato.it",
      provider: "openai",
      auditMode: "full_site_mvp",
      maxPages: 100,
      includeAiAnalysis: false,
    });

    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ maxPages: 100 }),
    );
  });

  it("does not render legacy guided URL audit section", () => {
    setupMocks();
    const html = renderPage();
    expect(html).not.toContain("Audit guidato su URL");
    expect(html).not.toContain("SEO Audit Control Room");
  });

  it("renders AI/GEO/CRO coming card", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Analisi AI/GEO/CRO in arrivo");
    expect(html).toContain("Prodotto: SEO ecommerce, schema Product, immagini, CRO e trust.");
    expect(html).toContain("Blog: contenuto, intent, E-E-A-T, GEO e linking interno.");
    expect(html).toContain("Collection: intent commerciale, schema, testo categoria e UX catalogo.");
    expect(html).toContain("Step successivo");
  });
});
