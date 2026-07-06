import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { DataForSeoCostSandboxPage, formatDataForSeoTestError } from "./DataForSeoCostSandboxPage";

const {
  useParamsMock,
  useProjectMock,
  useDataForSeoStatusMock,
  useDataForSeoUsageMock,
  useDataForSeoEstimateMock,
  useDataForSeoSandboxTestMock,
  useGrowthAuditRunsMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useDataForSeoStatusMock: vi.fn(),
  useDataForSeoUsageMock: vi.fn(),
  useDataForSeoEstimateMock: vi.fn(),
  useDataForSeoSandboxTestMock: vi.fn(),
  useGrowthAuditRunsMock: vi.fn(),
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

vi.mock("../hooks/useDataForSeo", () => ({
  useDataForSeoStatus: useDataForSeoStatusMock,
  useDataForSeoUsage: useDataForSeoUsageMock,
  useDataForSeoEstimate: useDataForSeoEstimateMock,
  useDataForSeoSandboxTest: useDataForSeoSandboxTestMock,
}));

vi.mock("../hooks/useGrowthAudit", () => ({
  useGrowthAuditRuns: useGrowthAuditRunsMock,
}));

function setupMocks(options?: {
  realCallsEnabled?: boolean;
  estimateData?: {
    mode: "single_page";
    estimatedCalls: { searchVolume: number; keywordIdeas: number; serp: number };
    estimatedCostUsd: number;
    assumptions: string[];
    budgetWarnings: string[];
  };
}) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
  });
  useDataForSeoStatusMock.mockReturnValue({
    data: {
      configured: true,
      realCallsEnabled: options?.realCallsEnabled ?? false,
      missingVars: [],
      singleRunLimitUsd: 0.2,
      dailyBudgetUsd: 1,
      monthlyBudgetUsd: 10,
      usageTodayUsd: 0,
      usageMonthUsd: 0,
    },
    isLoading: false,
  });
  useDataForSeoUsageMock.mockReturnValue({
    data: {
      logs: [
        {
          id: "log-1",
          endpoint: "/keywords_data/google_ads/search_volume/live",
          operation: "search_volume",
          status: "success",
          costUsd: 0.05,
          createdAt: "2026-07-06T10:00:00.000Z",
        },
      ],
      usageTodayUsd: 0.05,
      usageMonthUsd: 0.05,
      averageCostByOperation: { search_volume: 0.05 },
    },
    isLoading: false,
  });
  useDataForSeoEstimateMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
    data: options?.estimateData,
  });
  useDataForSeoSandboxTestMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
    data: null,
  });
  useGrowthAuditRunsMock.mockReturnValue({
    data: [
      {
        id: "run-1",
        status: "completed",
        normalizedDomain: "solmielato.it",
        createdAt: "2026-07-01T10:00:00.000Z",
      },
    ],
  });
}

function renderPage() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <DataForSeoCostSandboxPage />
    </MemoryRouter>,
  );
}

describe("DataForSeoCostSandboxPage", () => {
  it("shows keyword input", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Keyword");
    expect(html).toContain('value="polline biologico"');
  });

  it("updates estimate calls when mode changes in rendered output", () => {
    setupMocks({
      estimateData: {
        mode: "single_page",
        estimatedCalls: { searchVolume: 3, keywordIdeas: 3, serp: 1 },
        estimatedCostUsd: 0.55,
        assumptions: ["Modalità: single_page."],
        budgetWarnings: [],
      },
    });
    const html = renderPage();
    expect(html).toContain("search volume 3");
    expect(html).toContain("keyword ideas 3");
    expect(html).toContain("SERP 1");
    expect(html).toContain("$0.5500");
  });

  it("disables test button when real calls are disabled", () => {
    setupMocks({ realCallsEnabled: false });
    const html = renderPage();
    expect(html).toContain("disabled=");
    expect(html).toContain("DATAFORSEO_ENABLE_REAL_CALLS=true");
  });

  it("renders usage log rows", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Usage log");
    expect(html).toContain("search_volume");
    expect(html).toContain("$0.0500");
  });

  it("renders all test type options in select", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Search volume");
    expect(html).toContain("Keyword ideas");
    expect(html).toContain("SERP top 10");
    expect(html).toContain("Micro bundle");
    expect(html).toContain('value="search_volume"');
    expect(html).toContain('value="keyword_ideas"');
    expect(html).toContain('value="serp"');
    expect(html).toContain('value="micro_bundle"');
  });
});

describe("formatDataForSeoTestError", () => {
  it("maps validation errors to readable message", () => {
    expect(formatDataForSeoTestError(new Error("Field required"))).toBe(
      "Payload non valido: controlla keyword, location e lingua.",
    );
  });

  it("keeps real calls disabled message", () => {
    expect(formatDataForSeoTestError(new Error("DataForSEO real calls disabled."))).toBe(
      "DataForSEO real calls disabled.",
    );
  });
});
