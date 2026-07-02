import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { SeoSkillCatalogItem, SeoSkillRun, SeoSkillRunResult } from "@gcr/shared";
import { SeoAuditConfigurator } from "./SeoAuditConfigurator";
import { SeoAuditPresetCard } from "./SeoAuditPresetCard";
import { SeoAuditSummaryCard } from "./SeoAuditSummaryCard";
import { SeoSkillRunResultCard } from "./SeoSkillRunResultCard";
import { getAuditPreset } from "./seo-skill-presets";

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
    makeSkill(),
    makeSkill({ key: "seo_content", label: "Content SEO", category: "content" }),
    makeSkill({ key: "seo_schema", label: "Schema SEO", category: "structured_data" }),
  ];
}

function makeRun(overrides: Partial<SeoSkillRun> = {}): SeoSkillRun {
  return {
    id: "run-1",
    projectId: "proj-1",
    targetType: "url",
    url: "https://example.com/products/test",
    status: "completed",
    provider: "openai",
    selectedSkills: ["seo_page"],
    progressPercent: 100,
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

describe("SeoAuditPresetCard", () => {
  it("renders title and description", () => {
    const preset = getAuditPreset("page_360")!;
    const html = renderToStaticMarkup(
      <SeoAuditPresetCard
        preset={preset}
        selected={false}
        availableSkillCount={6}
        totalSkillCount={6}
        onSelect={() => undefined}
      />,
    );

    expect(html).toContain("Audit pagina 360°");
    expect(html).toContain("Analizza una singola pagina");
  });
});

describe("SeoAuditConfigurator", () => {
  it("disables CTA when URL is missing", () => {
    const preset = getAuditPreset("page_360")!;
    const html = renderToStaticMarkup(
      <SeoAuditConfigurator
        preset={preset}
        catalog={makeCatalog()}
        manualSkillKeys={new Set()}
        onToggleManualSkill={() => undefined}
        categoryFilter="all"
        onCategoryFilterChange={() => undefined}
        provider="openai"
        onProviderChange={() => undefined}
        targetUrl=""
        onTargetUrlChange={() => undefined}
        onSubmit={() => undefined}
        isSubmitting={false}
      />,
    );

    expect(html).toContain('disabled=""');
  });

  it("shows included skill chips", () => {
    const preset = getAuditPreset("page_360")!;
    const html = renderToStaticMarkup(
      <SeoAuditConfigurator
        preset={preset}
        catalog={makeCatalog()}
        manualSkillKeys={new Set()}
        onToggleManualSkill={() => undefined}
        categoryFilter="all"
        onCategoryFilterChange={() => undefined}
        provider="openai"
        onProviderChange={() => undefined}
        targetUrl="https://example.com"
        onTargetUrlChange={() => undefined}
        onSubmit={() => undefined}
        isSubmitting={false}
      />,
    );

    expect(html).toContain("Page SEO");
    expect(html).toContain("Skill incluse");
  });

  it("shows manual catalog section for custom preset", () => {
    const preset = getAuditPreset("custom")!;
    const html = renderToStaticMarkup(
      <SeoAuditConfigurator
        preset={preset}
        catalog={makeCatalog()}
        manualSkillKeys={new Set(["seo_page"])}
        onToggleManualSkill={() => undefined}
        categoryFilter="all"
        onCategoryFilterChange={() => undefined}
        provider="openai"
        onProviderChange={() => undefined}
        targetUrl="https://example.com"
        onTargetUrlChange={() => undefined}
        onSubmit={() => undefined}
        isSubmitting={false}
      />,
    );

    expect(html).toContain("Seleziona skill manualmente");
  });
});

describe("SeoAuditSummaryCard", () => {
  it("renders average score and priority issue counts", () => {
    const html = renderToStaticMarkup(
      <SeoAuditSummaryCard
        run={makeRun()}
        results={[
          makeResult({
            score: 82,
            findings: [
              { title: "Critical", severity: "critical" },
              { title: "High", severity: "high" },
            ],
            tasks: [{ title: "Task 1", description: "desc" }],
          }),
        ]}
      />,
    );

    expect(html).toContain("82");
    expect(html).toContain("Score complessivo");
    expect(html).toContain("Problemi prioritari");
    expect(html).toContain("Task da fare");
  });
});

describe("SeoSkillRunResultCard audit labels", () => {
  it("shows Come risolvere and Come verificare labels", () => {
    const html = renderToStaticMarkup(
      <SeoSkillRunResultCard
        result={makeResult({
          findings: [
            {
              title: "Meta mancante",
              severity: "high",
              description: "Manca meta description",
              recommendation: "Aggiungi meta description",
              howToValidate: "Controlla view-source",
            },
          ],
          tasks: [{ title: "Aggiorna meta", description: "desc", ownerType: "content" }],
        })}
        catalogSkills={makeCatalog()}
      />,
    );

    expect(html).toContain("Come risolvere");
    expect(html).toContain("Come verificare");
    expect(html).toContain("Azioni prioritarie");
  });
});
