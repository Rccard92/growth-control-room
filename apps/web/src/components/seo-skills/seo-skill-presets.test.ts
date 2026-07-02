import { describe, expect, it } from "vitest";
import type { SeoSkillCatalogItem } from "@gcr/shared";
import { getAuditPreset } from "./seo-skill-presets";
import { buildAuditDashboardSummary, resolvePresetSkills } from "./seo-skills-utils";

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

function makeCatalog(): SeoSkillCatalogItem[] {
  return [
    makeSkill({ key: "seo_page", label: "Page SEO" }),
    makeSkill({ key: "seo_content", label: "Content SEO", category: "content" }),
    makeSkill({ key: "seo_schema", label: "Schema SEO", category: "structured_data" }),
    makeSkill({ key: "seo_images", label: "Images SEO", category: "media" }),
    makeSkill({ key: "seo_geo", label: "GEO SEO", category: "ai_search" }),
    makeSkill({ key: "seo_sxo", label: "SXO SEO", category: "strategy" }),
    makeSkill({ key: "seo_ecommerce", label: "Ecommerce SEO", category: "ecommerce" }),
    makeSkill({ key: "seo_technical", label: "Technical SEO" }),
    makeSkill({ key: "seo_audit", label: "Site Audit" }),
    makeSkill({
      key: "seo_crawl",
      label: "Crawl SEO",
      status: "planned",
      runtime: "planned",
    }),
  ];
}

describe("seo-skill-presets", () => {
  it("page_360 includes the correct skills", () => {
    const preset = getAuditPreset("page_360");
    expect(preset).toBeDefined();
    expect(preset?.includedSkills).toEqual([
      "seo_page",
      "seo_content",
      "seo_schema",
      "seo_images",
      "seo_geo",
      "seo_sxo",
    ]);
  });

  it("product_page includes seo_ecommerce", () => {
    const preset = getAuditPreset("product_page");
    expect(preset?.includedSkills).toContain("seo_ecommerce");
  });
});

describe("resolvePresetSkills", () => {
  it("filters only available prompt_only skills", () => {
    const preset = getAuditPreset("page_360")!;
    const catalog = makeCatalog();
    const resolved = resolvePresetSkills(preset, catalog);

    expect(resolved.availableKeys).toEqual([
      "seo_page",
      "seo_content",
      "seo_schema",
      "seo_images",
      "seo_geo",
      "seo_sxo",
    ]);
    expect(resolved.unavailableKeys).toEqual([]);
  });

  it("marks unavailable preset skills", () => {
    const preset = getAuditPreset("page_360")!;
    const catalog = makeCatalog().filter((skill) => skill.key !== "seo_geo");
    const resolved = resolvePresetSkills(preset, catalog);

    expect(resolved.availableKeys).not.toContain("seo_geo");
    expect(resolved.unavailableKeys).toContain("seo_geo");
  });

  it("uses manual keys for custom preset", () => {
    const preset = getAuditPreset("custom")!;
    const catalog = makeCatalog();
    const resolved = resolvePresetSkills(preset, catalog, ["seo_page", "seo_content"]);

    expect(resolved.availableKeys).toEqual(["seo_page", "seo_content"]);
  });
});

describe("buildAuditDashboardSummary", () => {
  it("calculates average score and counts critical/high findings", () => {
    const summary = buildAuditDashboardSummary([
      {
        id: "1",
        runId: "run-1",
        projectId: "proj-1",
        skillKey: "seo_page",
        status: "completed",
        score: 80,
        findings: [
          { title: "Critical issue", severity: "critical" },
          { title: "High issue", severity: "high" },
        ],
        tasks: [{ title: "Fix title", description: "desc" }],
      },
      {
        id: "2",
        runId: "run-1",
        projectId: "proj-1",
        skillKey: "seo_content",
        status: "completed",
        score: 60,
        findings: [{ title: "Medium issue", severity: "medium" }],
        tasks: [{ title: "Fix content", description: "desc" }],
      },
    ]);

    expect(summary.averageScore).toBe(70);
    expect(summary.criticalCount).toBe(1);
    expect(summary.highCount).toBe(1);
    expect(summary.mediumCount).toBe(1);
    expect(summary.totalTasks).toBe(2);
    expect(summary.scoreBand).toBe("warn");
  });
});
