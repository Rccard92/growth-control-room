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
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useShopifyStatusMock: vi.fn(),
  useSeoSkillCatalogMock: vi.fn(),
  useSeoSkillRunsMock: vi.fn(),
  useSeoSkillRunMock: vi.fn(),
  useStartSeoSkillRunMock: vi.fn(),
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

function setupMocks() {
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

  it("shows Full Site Audit in preparation", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Full Site Audit");
    expect(html).toContain("In preparazione");
    expect(html).toContain("Prepara Full Audit");
  });

  it("renders guided URL audit section", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Audit guidato su URL");
    expect(html).toContain("SEO Audit Control Room");
  });
});
