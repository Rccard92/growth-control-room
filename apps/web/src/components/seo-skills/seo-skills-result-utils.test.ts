import { describe, expect, it } from "vitest";
import type { SeoSkillCatalogItem, SeoSkillRunResult } from "@gcr/shared";
import {
  buildRunPanelSummary,
  formatRunPanelHeadline,
  formatSeoSkillResultStatus,
  getResultArtifacts,
  getResultScore,
  getResultSummary,
  getSkillDisplayName,
  normalizeArtifacts,
  normalizeFindings,
  normalizeRecommendations,
  normalizeTasks,
} from "./seo-skills-utils";

function makeSkill(overrides: Partial<SeoSkillCatalogItem> = {}): SeoSkillCatalogItem {
  return {
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
    ...overrides,
  };
}

function makeResult(overrides: Partial<SeoSkillRunResult> = {}): SeoSkillRunResult {
  return {
    id: "result-1",
    runId: "run-1",
    projectId: "proj-1",
    skillKey: "seo_page",
    status: "completed",
    ...overrides,
  };
}

describe("normalizeFindings", () => {
  it("normalizes valid findings and sorts by severity", () => {
    const findings = normalizeFindings([
      { title: "Low issue", severity: "low", description: "desc" },
      { title: "Critical issue", severity: "critical", description: "desc" },
    ]);

    expect(findings).toHaveLength(2);
    expect(findings[0].title).toBe("Critical issue");
    expect(findings[0].severityLabel).toBe("Critico");
  });

  it("ignores malformed findings", () => {
    expect(normalizeFindings([{ foo: "bar" }, null, "text"])).toEqual([]);
  });
});

describe("normalizeRecommendations", () => {
  it("normalizes valid recommendations", () => {
    const items = normalizeRecommendations([
      {
        title: "Improve title",
        description: "Use keyword in H1",
        priority: "high",
        impact: "high",
        effort: "low",
      },
    ]);

    expect(items[0].title).toBe("Improve title");
    expect(items[0].priorityLabel).toBe("Alta");
    expect(items[0].effortLabel).toBe("Basso");
  });
});

describe("normalizeTasks", () => {
  it("normalizes valid tasks", () => {
    const items = normalizeTasks([
      {
        title: "Update meta",
        description: "Rewrite meta description",
        priority: "medium",
        ownerType: "content",
        estimatedEffort: "low",
      },
    ]);

    expect(items[0].ownerTypeLabel).toBe("Contenuto");
    expect(items[0].estimatedEffortLabel).toBe("Basso");
  });
});

describe("normalizeArtifacts", () => {
  it("normalizes artifacts with markdown and prompts", () => {
    const artifacts = normalizeArtifacts({
      jsonLd: [{ "@type": "Product", name: "Test" }],
      markdownReport: "# Report",
      shopifySidekickPrompts: ["Prompt 1"],
      implementationNotes: ["Note 1"],
    });

    expect(artifacts.markdownReport).toBe("# Report");
    expect(artifacts.shopifySidekickPrompts).toEqual(["Prompt 1"]);
    expect(artifacts.jsonLd).toHaveLength(1);
  });
});

describe("result helpers", () => {
  it("getSkillDisplayName uses catalog label when available", () => {
    expect(getSkillDisplayName("seo_page", [makeSkill()])).toBe("Page SEO");
    expect(getSkillDisplayName("seo_unknown", [])).toBe("seo_unknown");
  });

  it("getResultSummary reads summary from rawOutput", () => {
    const summary = getResultSummary(
      makeResult({
        rawOutput: {
          summary: "La pagina è ben strutturata.",
        },
      }),
    );
    expect(summary).toBe("La pagina è ben strutturata.");
  });

  it("getResultScore prefers result.score", () => {
    expect(getResultScore(makeResult({ score: 82 }))).toBe(82);
  });

  it("getResultArtifacts falls back to rawOutput artifacts", () => {
    const artifacts = getResultArtifacts(
      makeResult({
        rawOutput: {
          artifacts: {
            markdownReport: "Report breve",
            jsonLd: [],
            shopifySidekickPrompts: [],
            implementationNotes: [],
          },
        },
      }),
    );
    expect(artifacts.markdownReport).toBe("Report breve");
  });
});

describe("run panel helpers", () => {
  it("formatSeoSkillResultStatus maps completed", () => {
    expect(formatSeoSkillResultStatus("completed")).toBe("Completata");
  });

  it("formatRunPanelHeadline maps partial_failed", () => {
    expect(formatRunPanelHeadline("partial_failed")).toBe("Analisi completata con errori");
  });

  it("buildRunPanelSummary counts statuses", () => {
    const summary = buildRunPanelSummary([
      makeResult({ id: "1", status: "completed" }),
      makeResult({ id: "2", status: "failed", skillKey: "seo_geo" }),
      makeResult({ id: "3", status: "running", skillKey: "seo_schema" }),
    ]);

    expect(summary).toEqual({
      total: 3,
      completed: 1,
      failed: 1,
      running: 1,
      pending: 0,
    });
  });
});

describe("failed result data", () => {
  it("failed result exposes error message via result object", () => {
    const result = makeResult({
      status: "failed",
      errorMessage: "OpenAI non ha restituito un JSON valido.",
    });
    expect(result.errorMessage).toContain("JSON valido");
  });
});
