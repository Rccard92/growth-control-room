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
          rootUrl: "https://solmielato.myshopify.com",
          normalizedDomain: "solmielato.myshopify.com",
          status: "completed",
          phase: "completed",
          auditMode: "full_site_mvp",
          provider: "openai",
          progressPercent: 100,
          pagesDiscovered: 1,
          pagesClassified: 1,
          pagesAnalyzed: 0,
          pagesFailed: 0,
          summary: { message: "Audit skeleton completato." },
        },
        pages: [
          {
            id: "page-1",
            runId: "run-1",
            projectId: "proj-1",
            url: "https://solmielato.myshopify.com",
            normalizedUrl: "https://solmielato.myshopify.com",
            pageType: "homepage",
            source: "seed",
            status: "classified",
            priority: "high",
          },
        ],
        events: [
          {
            id: "evt-1",
            runId: "run-1",
            projectId: "proj-1",
            eventType: "run_completed",
            phase: "completed",
            message: "Growth Audit completato",
            progressPercent: 100,
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
    mutateAsync: vi.fn(),
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

  it("renders URL input and start CTA", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Dominio o URL principale");
    expect(html).toContain("Avvia Full Site Audit");
    expect(html).toContain("https://solmielato.myshopify.com");
  });

  it("shows active run progress and pages when run exists", () => {
    setupMocks({ withActiveRun: true });
    const html = renderPage();
    expect(html).toContain("Run attiva");
    expect(html).toContain("Completato");
    expect(html).toContain("Audit skeleton completato.");
    expect(html).toContain("Homepage");
    expect(html).toContain("Ultimi eventi");
  });

  it("renders guided URL audit section", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Audit guidato su URL");
    expect(html).toContain("SEO Audit Control Room");
  });
});
