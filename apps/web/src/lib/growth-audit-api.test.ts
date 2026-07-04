import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "./api";

describe("growth-audit-api", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, "apiFetch").mockResolvedValue({});
  });

  it("calls start run endpoint with POST body", async () => {
    const { startGrowthAuditRun } = await import("./growth-audit-api");
    const payload = {
      rootUrl: "https://example.com",
      provider: "openai" as const,
      auditMode: "full_site_mvp" as const,
      maxPages: 50,
      includeAiAnalysis: false,
    };
    await startGrowthAuditRun("proj-1", payload);
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
  });

  it("calls list runs endpoint", async () => {
    const { listGrowthAuditRuns } = await import("./growth-audit-api");
    await listGrowthAuditRuns("proj-1");
    expect(api.apiFetch).toHaveBeenCalledWith("/api/projects/proj-1/growth-audit/runs");
  });

  it("calls run detail endpoint", async () => {
    const { fetchGrowthAuditRun } = await import("./growth-audit-api");
    await fetchGrowthAuditRun("proj-1", "run-42");
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42",
    );
  });

  it("calls pages endpoint", async () => {
    const { fetchGrowthAuditPages } = await import("./growth-audit-api");
    await fetchGrowthAuditPages("proj-1", "run-42");
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/pages",
    );
  });

  it("calls events endpoint", async () => {
    const { fetchGrowthAuditEvents } = await import("./growth-audit-api");
    await fetchGrowthAuditEvents("proj-1", "run-42");
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/events",
    );
  });
});
