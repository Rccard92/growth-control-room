import { beforeEach, describe, expect, it, vi } from "vitest";
import type { GrowthAuditPage, GrowthAuditRun } from "@gcr/shared";
import { queryKeys } from "../lib/queryKeys";

const invalidateQueriesMock = vi.fn();
const rescanGrowthAuditPageMock = vi.fn();
const analyzeGrowthAuditPageWithAiMock = vi.fn();
const analyzeGrowthAuditShopifyCommerceMock = vi.fn();

let capturedMutation: {
  mutationFn: (input: unknown) => Promise<unknown>;
  onSuccess?: (data: unknown) => void;
} | null = null;

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries: invalidateQueriesMock,
  }),
  useMutation: (config: typeof capturedMutation) => {
    capturedMutation = config;
    return {
      mutateAsync: config?.mutationFn,
      isPending: false,
    };
  },
  useQuery: vi.fn(),
}));

vi.mock("../lib/growth-audit-api", () => ({
  rescanGrowthAuditPage: rescanGrowthAuditPageMock,
  analyzeGrowthAuditPageWithAi: analyzeGrowthAuditPageWithAiMock,
  analyzeGrowthAuditShopifyCommerce: analyzeGrowthAuditShopifyCommerceMock,
  fetchGrowthAuditPageResults: vi.fn(),
  startGrowthAuditRun: vi.fn(),
  listGrowthAuditRuns: vi.fn(),
  fetchGrowthAuditRun: vi.fn(),
  fetchGrowthAuditPages: vi.fn(),
  fetchGrowthAuditEvents: vi.fn(),
  fetchGrowthAuditFindings: vi.fn(),
  fetchGrowthAuditTasks: vi.fn(),
}));

describe("useRescanGrowthAuditPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedMutation = null;
  });

  it("invalidates growth audit queries on success", async () => {
    const { useRescanGrowthAuditPage } = await import("./useGrowthAudit");
    useRescanGrowthAuditPage("proj-1");

    expect(capturedMutation).not.toBeNull();

    const response = {
      run: { id: "run-42" } as GrowthAuditRun,
      page: { id: "page-1" } as GrowthAuditPage,
      findingsCount: 2,
      tasksCount: 1,
      message: "Pagina riscansionata.",
    };

    capturedMutation!.onSuccess?.(response);

    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.runs("proj-1"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.run("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.pages("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.findings("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.tasks("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.events("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledTimes(6);
  });

  it("calls rescan API with project, run and page ids", async () => {
    const { useRescanGrowthAuditPage } = await import("./useGrowthAudit");
    rescanGrowthAuditPageMock.mockResolvedValue({
      run: { id: "run-42" },
      page: { id: "page-1" },
      findingsCount: 0,
      tasksCount: 0,
      message: "ok",
    });

    const hook = useRescanGrowthAuditPage("proj-1");
    await hook.mutateAsync({
      runId: "run-42",
      pageId: "page-1",
      payload: { clearPreviousOpenItems: false },
    });

    expect(rescanGrowthAuditPageMock).toHaveBeenCalledWith(
      "proj-1",
      "run-42",
      "page-1",
      { clearPreviousOpenItems: false },
    );
  });
});

describe("useAnalyzeGrowthAuditPageWithAi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedMutation = null;
  });

  it("invalidates growth audit queries including page results on success", async () => {
    const { useAnalyzeGrowthAuditPageWithAi } = await import("./useGrowthAudit");
    useAnalyzeGrowthAuditPageWithAi("proj-1", "run-42");

    expect(capturedMutation).not.toBeNull();

    const response = {
      run: { id: "run-42" } as GrowthAuditRun,
      page: { id: "page-7" } as GrowthAuditPage,
      result: { id: "result-1" },
      findingsCount: 3,
      tasksCount: 2,
      message: "Analisi completata.",
    };

    capturedMutation!.onSuccess?.(response);

    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.pageResults("proj-1", "run-42", "page-7"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledTimes(7);
  });

  it("calls ai analysis API with project, run and page ids", async () => {
    const { useAnalyzeGrowthAuditPageWithAi } = await import("./useGrowthAudit");
    analyzeGrowthAuditPageWithAiMock.mockResolvedValue({
      run: { id: "run-42" },
      page: { id: "page-7" },
      result: { id: "result-1" },
      findingsCount: 1,
      tasksCount: 1,
      message: "ok",
    });

    const hook = useAnalyzeGrowthAuditPageWithAi("proj-1", "run-42");
    await hook.mutateAsync({
      pageId: "page-7",
      payload: { provider: "openai", includeGeo: false },
    });

    expect(analyzeGrowthAuditPageWithAiMock).toHaveBeenCalledWith(
      "proj-1",
      "run-42",
      "page-7",
      { provider: "openai", includeGeo: false },
    );
  });
});

describe("useAnalyzeGrowthAuditShopifyCommerce", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedMutation = null;
  });

  it("invalidates growth audit queries on success", async () => {
    const { useAnalyzeGrowthAuditShopifyCommerce } = await import("./useGrowthAudit");
    useAnalyzeGrowthAuditShopifyCommerce("proj-1", "run-42");

    expect(capturedMutation).not.toBeNull();

    const response = {
      run: { id: "run-42" } as GrowthAuditRun,
      summary: { totalSales: 120 },
      message: "Dati ecommerce Shopify aggiornati",
    };

    capturedMutation!.onSuccess?.(response);

    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.runs("proj-1"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.run("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.pages("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.findings("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.tasks("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledWith({
      queryKey: queryKeys.growthAudit.events("proj-1", "run-42"),
    });
    expect(invalidateQueriesMock).toHaveBeenCalledTimes(6);
  });

  it("calls shopify commerce API with project and run ids", async () => {
    const { useAnalyzeGrowthAuditShopifyCommerce } = await import("./useGrowthAudit");
    analyzeGrowthAuditShopifyCommerceMock.mockResolvedValue({
      run: { id: "run-42" },
      summary: { totalSales: 50 },
      message: "ok",
    });

    const hook = useAnalyzeGrowthAuditShopifyCommerce("proj-1", "run-42");
    await hook.mutateAsync({ days: 30 });

    expect(analyzeGrowthAuditShopifyCommerceMock).toHaveBeenCalledWith(
      "proj-1",
      "run-42",
      { days: 30 },
    );
  });
});
