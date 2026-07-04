import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { GrowthAuditPage } from "./GrowthAuditPage";

const {
  useParamsMock,
  useProjectMock,
  useShopifyStatusMock,
  useSeoSkillCatalogMock,
  useSeoSkillRunsMock,
  useSeoSkillRunMock,
  useStartSeoSkillRunMock,
  useGrowthAuditRunsMock,
  useGrowthAuditRunMock,
  useStartGrowthAuditRunMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useShopifyStatusMock: vi.fn(),
  useSeoSkillCatalogMock: vi.fn(),
  useSeoSkillRunsMock: vi.fn(),
  useSeoSkillRunMock: vi.fn(),
  useStartSeoSkillRunMock: vi.fn(),
  useGrowthAuditRunsMock: vi.fn(),
  useGrowthAuditRunMock: vi.fn(),
  useStartGrowthAuditRunMock: vi.fn(),
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

vi.mock("../hooks/useSeoSkills", () => ({
  useSeoSkillCatalog: useSeoSkillCatalogMock,
  useSeoSkillRuns: useSeoSkillRunsMock,
  useSeoSkillRun: useSeoSkillRunMock,
  useStartSeoSkillRun: useStartSeoSkillRunMock,
}));

vi.mock("../hooks/useGrowthAudit", () => ({
  useGrowthAuditRuns: useGrowthAuditRunsMock,
  useGrowthAuditRun: useGrowthAuditRunMock,
  useStartGrowthAuditRun: useStartGrowthAuditRunMock,
}));

function setupMocks(options?: { withActiveRun?: boolean }) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
    isLoading: false,
  });
  useShopifyStatusMock.mockReturnValue({
    data: { connected: true, shopDomain: "solmielato.myshopify.com" },
  });
  useSeoSkillCatalogMock.mockReturnValue({
    data: {
      skills: [
        {
          key: "seo_page",
          label: "Page SEO",
          description: "Page SEO",
          category: "audit",
          source: "claude-seo",
          upstreamCommand: "/seo page",
          status: "available",
          defaultProvider: "openai",
          requires: ["url"],
          optionalIntegrations: [],
          requiredIntegrations: [],
          outputSchema: "seo_page_v1",
          runtime: "prompt_only",
          riskLevel: "low",
          enabled: true,
        },
      ],
      counts: { total: 1, available: 1, needsConfig: 0, externalRequired: 0, planned: 0 },
    },
    isLoading: false,
    isError: false,
  });
  useSeoSkillRunsMock.mockReturnValue({ data: [] });
  useSeoSkillRunMock.mockReturnValue({ data: undefined, isLoading: false });
  useStartSeoSkillRunMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });

  const activeRun = options?.withActiveRun
    ? {
        run: {
          id: "run-1",
          projectId: "proj-1",
          rootUrl: "https://solmielato.it",
          normalizedDomain: "solmielato.it",
          status: "completed",
          phase: "finalization",
          auditMode: "full_site_mvp",
          provider: "openai",
          progressPercent: 100,
          pagesDiscovered: 3,
          pagesClassified: 3,
          pagesAnalyzed: 0,
          pagesFailed: 0,
          summary: {
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
            status: "classified",
            priority: "high",
            title: "Home",
          },
          {
            id: "page-2",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.it/products/miele",
            normalizedUrl: "https://solmielato.it/products/miele",
            pageType: "product",
            source: "shopify_product",
            status: "classified",
            priority: "normal",
            title: "Miele",
          },
          {
            id: "page-3",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.it/collections/best",
            normalizedUrl: "https://solmielato.it/collections/best",
            pageType: "collection",
            source: "sitemap",
            status: "classified",
            priority: "normal",
            title: "Best",
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
  useStartGrowthAuditRunMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({ run: { id: "run-new" } }),
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
    setupMocks({ withActiveRun: true });
    const html = renderPage();
    expect(html).toContain("Inventario pagine");
    expect(html).toContain("Homepage");
    expect(html).toContain("Shopify prodotto");
    expect(html).toContain("Sitemap");
    expect(html).toContain("Analisi in arrivo");
    expect(html).toContain("Prodotti");
    expect(html).toContain("Categorie");
    expect(html).toContain("Eventi recenti");
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

  it("renders guided URL audit section", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Audit guidato su URL");
    expect(html).toContain("SEO Audit Control Room");
  });
});
