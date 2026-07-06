import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "./api";

describe("dataforseo-api", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, "apiFetch").mockResolvedValue({});
  });

  it("calls sandbox test endpoint with camelCase POST body", async () => {
    const { runDataForSeoSandboxTest } = await import("./dataforseo-api");
    const payload = {
      testType: "search_volume" as const,
      keyword: "polline biologico",
      locationCode: 2380,
      languageCode: "it",
    };
    await runDataForSeoSandboxTest("proj-1", payload);
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/dataforseo/cost-sandbox/test",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
  });

  it("calls estimate endpoint with camelCase POST body", async () => {
    const { estimateDataForSeoCost } = await import("./dataforseo-api");
    const payload = {
      mode: "single_page" as const,
      runId: "run-1",
      seedQueriesPerPage: 3,
      keywordIdeasPerSeed: 10,
      serpQueriesPerPage: 1,
    };
    await estimateDataForSeoCost("proj-1", payload);
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/dataforseo/cost-sandbox/estimate",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
  });
});
