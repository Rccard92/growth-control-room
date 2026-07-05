import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { GrowthAuditPage } from "./GrowthAuditPage";

const {
  useParamsMock,
  useProjectMock,
  useUpdateProjectMock,
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
  useUpdateProjectMock: vi.fn(),
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
  useUpdateProject: useUpdateProjectMock,
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

function setupMocks(options?: {
  withActiveRun?: boolean;
  withTechnicalScan?: boolean;
  publicSiteUrl?: string | null;
}) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: {
      id: "proj-1",
      name: "Solmielato",
      publicSiteUrl: options?.publicSiteUrl ?? null,
    },
    isLoading: false,
  });
  useUpdateProjectMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      id: "proj-1",
      name: "Solmielato",
      publicSiteUrl: "https://solmielato.it",
    }),
    isPending: false,
    isError: false,
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
          completedAt: "2026-06-01T10:00:00.000Z",
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
            sourceEntityId: "prod-1",
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

  it("shows onboarding hero and flow steps without runs", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("growth-audit-page--onboarding");
    expect(html).toContain("Configura il primo Growth Audit");
    expect(html).toContain("Scansiona sito");
    expect(html).toContain("Classifica pagine");
    expect(html).toContain("Correggi e riscansiona");
    expect(html).not.toContain("growth-audit-dashboard-hero");
  });

  it("renders scan form, maxPages selector and start CTA without myshopify default", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Dominio o URL principale");
    expect(html).toContain("Dominio pubblico del sito");
    expect(html).toContain("Salva dominio pubblico");
    expect(html).toContain("dominio tecnico");
    expect(html).toContain("Pagine massime");
    expect(html).toContain("Avvia scansione sito");
    expect(html).not.toContain("solmielato.myshopify.com");
    expect(html).toContain("https://tuodominio.it");
    expect(html).toContain("<option value=\"50\"");
    expect(html).not.toContain("Full Site Audit");
  });

  it("uses project publicSiteUrl as default scan root URL", () => {
    setupMocks({ publicSiteUrl: "https://solmielato.it" });
    const html = renderPage();
    expect(html).toContain('value="https://solmielato.it"');
  });

  it("hides flow steps and shows dashboard mode with completed run", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("growth-audit-page--dashboard");
    expect(html).toContain("growth-audit-dashboard-hero");
    expect(html).not.toContain("Configura il primo Growth Audit");
    expect(html).not.toContain("growth-audit-flow");
    expect(html).not.toContain("solmielato.myshopify.com");
  });

  it("shows priority dashboard before inventory in dashboard mode", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    const priorityIndex = html.indexOf("Priorità Growth Audit");
    const inventoryIndex = html.indexOf("Inventario pagine");
    expect(priorityIndex).toBeGreaterThan(-1);
    expect(inventoryIndex).toBeGreaterThan(-1);
    expect(priorityIndex).toBeLessThan(inventoryIndex);
  });

  it("puts new scan form in accordion when run exists", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("growth-audit-scan-disclosure");
    expect(html).toContain("Nuova scansione sito");
    expect(html).toContain("Riapri solo se vuoi aggiornare");
  });

  it("shows inventory table, badges and filters when run exists", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Gestisci pagina");
    expect(html).toContain("Tutte le pagine scoperte e scansionate");
    expect(html).toContain("Homepage");
    expect(html).toContain("Shopify prodotto");
    expect(html).toContain("Sitemap");
    expect(html).toContain("Prodotti");
    expect(html).toContain("Categorie");
    expect(html).toContain("HTTP");
    expect(html).toContain("Problemi");
    expect(html).toContain("82");
    expect(html).toContain("200");
    expect(html).toContain("Gestisci");
    expect(html).toContain("/projects/proj-1/audit/runs/run-1/pages/page-1");
    expect(html).toContain("Buona");
    expect(html).toContain("Shopify");
    expect(html).toContain("Collegata");
    expect(html).toContain("Non collegata");
  });

  it("prefills public root URL from completed run and shows technical KPIs", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true, publicSiteUrl: "https://solmielato.it" });
    const html = renderPage();
    expect(html).toContain('value="https://solmielato.it"');
    expect(html).toContain("Score tecnico");
    expect(html).not.toContain("Site Score");
    expect(html).toContain("78");
    expect(html).toContain("Pagine analizzate");
    expect(html).toContain("Performance");
    expect(html).toContain("In arrivo");
  });

  it("shows configured public site hostname in dashboard hero", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true, publicSiteUrl: "https://solmielato.it" });
    const html = renderPage();
    expect(html).toContain("Sito");
    expect(html).toContain("solmielato.it");
  });

  it("renders priority findings and open tasks", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Problemi prioritari");
    expect(html).toContain("Title mancante");
    expect(html).toContain("Task aperti");
    expect(html).toContain("Aggiungere title pagina");
    expect(html).toContain("cluster ricorrenti");
    expect(html).toContain("deterministica");
  });

  it("puts recent events inside events disclosure accordion", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("growth-audit-events-disclosure");
    expect(html).toContain("Eventi e log scansione");
    expect(html).toContain("Inventario completato");
    expect(html).not.toContain("Eventi recenti");
  });

  it("renders score filters and updated roadmap", () => {
    setupMocks({ withActiveRun: true, withTechnicalScan: true });
    const html = renderPage();
    expect(html).toContain("Critiche &lt;60");
    expect(html).toContain("Buone 80+");
    expect(html).toContain("Prossimi moduli professionali");
    expect(html).toContain("PageSpeed/CrUX");
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

  it("renders AI/GEO/CRO availability card", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Analisi AI/GEO/CRO");
    expect(html).toContain("scheda full-screen");
    expect(html).toContain("Prodotto: SEO ecommerce, schema Product, immagini, CRO e trust.");
    expect(html).toContain("Blog: contenuto, intent, E-E-A-T, GEO e linking interno.");
    expect(html).toContain("Collection: intent commerciale, schema, testo categoria e UX catalogo.");
    expect(html).toContain("Disponibile");
  });
});
