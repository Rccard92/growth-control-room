import { describe, expect, it } from "vitest";
import type { SeoSkillCatalogItem, SeoSkillRunResult } from "@gcr/shared";
import {
  buildRunResultsSummary,
  canSubmitLauncher,
  formatDefaultProvider,
  formatSeoSkillRunError,
  formatSeoSkillRunStatus,
  formatSkillRuntime,
  getSkillDisabledReason,
  isSkillSelectable,
  matchesCategoryFilter,
} from "./seo-skills-utils";

function makeSkill(overrides: Partial<SeoSkillCatalogItem> = {}): SeoSkillCatalogItem {
  return {
    key: "seo_audit",
    label: "SEO Audit",
    description: "Audit",
    category: "audit",
    source: "claude-seo",
    upstreamCommand: "/seo audit <url>",
    status: "available",
    defaultProvider: "claude",
    requires: ["url"],
    optionalIntegrations: [],
    requiredIntegrations: [],
    outputSchema: "seo_audit_v1",
    runtime: "prompt_only",
    riskLevel: "low",
    enabled: true,
    ...overrides,
  };
}

describe("isSkillSelectable", () => {
  it("returns true for available prompt_only skill", () => {
    expect(isSkillSelectable(makeSkill())).toBe(true);
  });

  it("returns false for needs_config status", () => {
    expect(isSkillSelectable(makeSkill({ status: "needs_config" }))).toBe(false);
  });
});

describe("getSkillDisabledReason", () => {
  it("returns configuration message for needs_config", () => {
    expect(getSkillDisabledReason(makeSkill({ status: "needs_config" }))).toBe(
      "Richiede configurazione",
    );
  });

  it("returns runtime message for non prompt_only", () => {
    expect(
      getSkillDisabledReason(makeSkill({ runtime: "connector_required" })),
    ).toBe("Runtime non ancora supportato");
  });
});

describe("formatSeoSkillRunStatus", () => {
  it("maps partial_failed to Italian label", () => {
    expect(formatSeoSkillRunStatus("partial_failed")).toBe("Completata con errori");
  });
});

describe("formatSkillRuntime", () => {
  it("maps prompt_only to Analisi AI", () => {
    expect(formatSkillRuntime("prompt_only")).toBe("Analisi AI");
  });
});

describe("formatDefaultProvider", () => {
  it("shows provider predefinito label", () => {
    expect(formatDefaultProvider("claude")).toBe("Provider predefinito: Claude");
  });
});

describe("buildRunResultsSummary", () => {
  it("summarizes completed and failed skills", () => {
    const skills = new Map<string, SeoSkillCatalogItem>([
      [
        "seo_page",
        {
          ...makeSkill(),
          key: "seo_page",
          label: "Page SEO",
        },
      ],
    ]);
    const results: SeoSkillRunResult[] = [
      {
        id: "1",
        runId: "run-1",
        projectId: "proj-1",
        skillKey: "seo_geo",
        status: "completed",
      },
      {
        id: "2",
        runId: "run-1",
        projectId: "proj-1",
        skillKey: "seo_page",
        status: "failed",
        errorMessage: "OpenAI ha restituito una risposta vuota.",
      },
    ];

    const summary = buildRunResultsSummary(results, skills);
    expect(summary).toEqual({
      selectedCount: 2,
      completedCount: 1,
      failedCount: 1,
      firstFailure: {
        label: "Page SEO",
        errorMessage: "OpenAI ha restituito una risposta vuota.",
      },
    });
  });
});

describe("canSubmitLauncher", () => {
  it("disables submit without URL or skills", () => {
    expect(canSubmitLauncher({ selectedCount: 0, targetUrl: "", isSubmitting: false })).toBe(
      false,
    );
    expect(canSubmitLauncher({ selectedCount: 2, targetUrl: "  ", isSubmitting: false })).toBe(
      false,
    );
  });

  it("enables submit when valid", () => {
    expect(
      canSubmitLauncher({
        selectedCount: 1,
        targetUrl: "https://example.com",
        isSubmitting: false,
      }),
    ).toBe(true);
  });
});

describe("formatSeoSkillRunError", () => {
  it("maps Claude provider error", () => {
    expect(
      formatSeoSkillRunError(new Error("Claude provider is not configured")),
    ).toBe("Provider Claude non configurato sul backend.");
  });

  it("maps generic error", () => {
    expect(formatSeoSkillRunError(new Error("Something went wrong"))).toBe(
      "Something went wrong",
    );
  });
});

describe("matchesCategoryFilter", () => {
  it("matches structured_data with schema filter", () => {
    expect(
      matchesCategoryFilter(makeSkill({ category: "structured_data" }), "schema"),
    ).toBe(true);
  });

  it("matches media with images filter", () => {
    expect(matchesCategoryFilter(makeSkill({ category: "media" }), "images")).toBe(true);
  });
});
