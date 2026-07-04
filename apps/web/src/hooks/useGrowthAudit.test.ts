import { beforeEach, describe, expect, it, vi } from "vitest";
import type { GrowthAuditPage, GrowthAuditRun } from "@gcr/shared";
import { queryKeys } from "../lib/queryKeys";

const invalidateQueriesMock = vi.fn();
const rescanGrowthAuditPageMock = vi.fn();

let capturedMutation: {
  mutationFn: (input: {
    runId: string;
    pageId: string;
    payload?: { clearPreviousOpenItems?: boolean };
  }) => Promise<unknown>;
  onSuccess?: (data: {
    run: GrowthAuditRun;
    page: GrowthAuditPage;
    findingsCount: number;
    tasksCount: number;
    message: string;
  }) => void;
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
