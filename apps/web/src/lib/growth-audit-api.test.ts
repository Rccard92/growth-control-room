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

  it("calls findings endpoint with filters", async () => {
    const { fetchGrowthAuditFindings } = await import("./growth-audit-api");
    await fetchGrowthAuditFindings("proj-1", "run-42", {
      severity: "high",
      pageId: "page-1",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/findings?severity=high&pageId=page-1",
    );
  });

  it("calls tasks endpoint with filters", async () => {
    const { fetchGrowthAuditTasks } = await import("./growth-audit-api");
    await fetchGrowthAuditTasks("proj-1", "run-42", {
      status: "open",
      ownerType: "seo",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/tasks?status=open&ownerType=seo",
    );
  });

  it("calls rescan page endpoint with POST body", async () => {
    const { rescanGrowthAuditPage } = await import("./growth-audit-api");
    await rescanGrowthAuditPage("proj-1", "run-42", "page-7", {
      clearPreviousOpenItems: true,
      note: "Dopo fix meta",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/pages/page-7/rescan",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          clearPreviousOpenItems: true,
          note: "Dopo fix meta",
        }),
      }),
    );
  });

  it("calls ai-analysis page endpoint with POST body", async () => {
    const { analyzeGrowthAuditPageWithAi } = await import("./growth-audit-api");
    await analyzeGrowthAuditPageWithAi("proj-1", "run-42", "page-7", {
      provider: "claude",
      includeSeo: true,
      includeGeo: false,
      includeCro: true,
      includeAdsReadiness: true,
      note: "Pagina prioritaria",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/pages/page-7/ai-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          provider: "claude",
          includeSeo: true,
          includeGeo: false,
          includeCro: true,
          includeAdsReadiness: true,
          note: "Pagina prioritaria",
        }),
      }),
    );
  });

  it("calls page results endpoint with resultType filter", async () => {
    const { fetchGrowthAuditPageResults } = await import("./growth-audit-api");
    await fetchGrowthAuditPageResults("proj-1", "run-42", "page-7", {
      resultType: "ai_deep_analysis",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/pages/page-7/results?resultType=ai_deep_analysis",
    );
  });

  it("calls performance-analysis page endpoint with POST body", async () => {
    const { analyzeGrowthAuditPagePerformance } = await import("./growth-audit-api");
    await analyzeGrowthAuditPagePerformance("proj-1", "run-42", "page-7", {
      strategy: "desktop",
    });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/pages/page-7/performance-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ strategy: "desktop" }),
      }),
    );
  });

  it("calls search-console-analysis run endpoint with POST body", async () => {
    const { analyzeGrowthAuditSearchConsole } = await import("./growth-audit-api");
    await analyzeGrowthAuditSearchConsole("proj-1", "run-42", { days: 28 });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/search-console-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ days: 28 }),
      }),
    );
  });

  it("calls analytics-analysis run endpoint with POST body", async () => {
    const { analyzeGrowthAuditAnalytics } = await import("./growth-audit-api");
    await analyzeGrowthAuditAnalytics("proj-1", "run-42", { days: 28 });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/analytics-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ days: 28 }),
      }),
    );
  });

  it("calls shopify-commerce-analysis run endpoint with POST body", async () => {
    const { analyzeGrowthAuditShopifyCommerce } = await import("./growth-audit-api");
    await analyzeGrowthAuditShopifyCommerce("proj-1", "run-42", { days: 30 });
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/growth-audit/runs/run-42/shopify-commerce-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ days: 30 }),
      }),
    );
  });
});
