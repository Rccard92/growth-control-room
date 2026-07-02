import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "./api";

describe("seo-skills-api", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, "apiFetch").mockResolvedValue({});
  });

  it("calls catalog endpoint", async () => {
    const { fetchSeoSkillCatalog } = await import("./seo-skills-api");
    await fetchSeoSkillCatalog("proj-1");
    expect(api.apiFetch).toHaveBeenCalledWith("/api/projects/proj-1/seo-skills/catalog");
  });

  it("calls start run endpoint with POST body", async () => {
    const { startSeoSkillRun } = await import("./seo-skills-api");
    const payload = {
      targetType: "url" as const,
      url: "https://example.com",
      selectedSkills: ["meta-audit"],
      provider: "claude" as const,
    };
    await startSeoSkillRun("proj-1", payload);
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/seo-skills/runs",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
  });

  it("calls list runs endpoint with default limit", async () => {
    const { listSeoSkillRuns } = await import("./seo-skills-api");
    await listSeoSkillRuns("proj-1");
    expect(api.apiFetch).toHaveBeenCalledWith("/api/projects/proj-1/seo-skills/runs");
  });

  it("calls list runs endpoint with custom limit", async () => {
    const { listSeoSkillRuns } = await import("./seo-skills-api");
    await listSeoSkillRuns("proj-1", 5);
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/seo-skills/runs?limit=5",
    );
  });

  it("calls run detail endpoint", async () => {
    const { fetchSeoSkillRun } = await import("./seo-skills-api");
    await fetchSeoSkillRun("proj-1", "run-42");
    expect(api.apiFetch).toHaveBeenCalledWith("/api/projects/proj-1/seo-skills/runs/run-42");
  });

  it("calls run results endpoint", async () => {
    const { fetchSeoSkillRunResults } = await import("./seo-skills-api");
    await fetchSeoSkillRunResults("proj-1", "run-42");
    expect(api.apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/seo-skills/runs/run-42/results",
    );
  });
});
