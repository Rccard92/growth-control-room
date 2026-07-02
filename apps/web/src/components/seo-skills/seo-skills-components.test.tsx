import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { SeoSkillCatalogItem, SeoSkillRun, SeoSkillRunResult } from "@gcr/shared";
import { SeoSkillArtifactsPanel } from "./SeoSkillArtifactsPanel";
import { SeoSkillRunPanel } from "./SeoSkillRunPanel";
import { SeoSkillRunResultCard } from "./SeoSkillRunResultCard";
import { normalizeArtifacts } from "./seo-skills-utils";

const { useSeoSkillRunMock } = vi.hoisted(() => ({
  useSeoSkillRunMock: vi.fn(),
}));

vi.mock("../../hooks/useSeoSkills", () => ({
  useSeoSkillRun: useSeoSkillRunMock,
}));

function makeSkill(): SeoSkillCatalogItem {
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
  };
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
    startedAt: "2026-06-13T10:00:00.000Z",
    completedAt: "2026-06-13T10:05:00.000Z",
    createdAt: "2026-06-13T10:00:00.000Z",
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

describe("SeoSkillRunResultCard", () => {
  it("renders skill label, score, summary, finding and task titles", () => {
    const html = renderToStaticMarkup(
      <SeoSkillRunResultCard
        result={makeResult({
          score: 82,
          rawOutput: {
            summary: "La pagina è ben strutturata.",
          },
          findings: [
            {
              title: "Meta description mancante",
              severity: "high",
              description: "Aggiungere meta description.",
            },
          ],
          tasks: [
            {
              title: "Aggiorna meta title",
              description: "Inserire keyword principale.",
              ownerType: "content",
            },
          ],
        })}
        catalogSkills={[makeSkill()]}
      />,
    );

    expect(html).toContain("Page SEO");
    expect(html).toContain("82");
    expect(html).toContain("La pagina è ben strutturata.");
    expect(html).toContain("Meta description mancante");
    expect(html).toContain("Aggiorna meta title");
    expect(html).toContain("Debug JSON");
    expect(html).toContain("<details");
  });

  it("renders error message for failed results", () => {
    const html = renderToStaticMarkup(
      <SeoSkillRunResultCard
        result={makeResult({
          status: "failed",
          errorMessage: "OpenAI non ha restituito un JSON valido.",
        })}
        catalogSkills={[makeSkill()]}
      />,
    );

    expect(html).toContain("seo-skill-result-card--failed");
    expect(html).toContain("OpenAI non ha restituito un JSON valido.");
  });
});

describe("SeoSkillArtifactsPanel", () => {
  it("renders markdown report and Sidekick prompts with copy buttons", () => {
    const artifacts = normalizeArtifacts({
      markdownReport: "# Report SEO",
      shopifySidekickPrompts: ["Ottimizza il titolo prodotto"],
      jsonLd: [],
      implementationNotes: [],
    });

    const html = renderToStaticMarkup(<SeoSkillArtifactsPanel artifacts={artifacts} />);

    expect(html).toContain("Report markdown");
    expect(html).toContain("# Report SEO");
    expect(html).toContain("Shopify Sidekick prompts");
    expect(html).toContain("Ottimizza il titolo prodotto");
    expect(html).toContain("Copia prompt");
  });
});

describe("SeoSkillRunPanel", () => {
  it("renders completed run summary", () => {
    useSeoSkillRunMock.mockReturnValue({
      data: {
        run: makeRun({ status: "completed" }),
        results: [makeResult({ status: "completed" })],
      },
      isLoading: false,
    });

    const html = renderToStaticMarkup(
      <SeoSkillRunPanel projectId="proj-1" runId="run-1" catalogSkills={[makeSkill()]} />,
    );

    expect(html).toContain("Analisi completata");
    expect(html).toContain("Risultati analisi");
    expect(html).toContain("Skill completate");
    expect(html).toContain("Page SEO");
  });

  it("renders failed run headline", () => {
    useSeoSkillRunMock.mockReturnValue({
      data: {
        run: makeRun({
          status: "failed",
          errorMessage: "Run fallita.",
        }),
        results: [makeResult({ status: "failed", errorMessage: "Skill fallita." })],
      },
      isLoading: false,
    });

    const html = renderToStaticMarkup(
      <SeoSkillRunPanel projectId="proj-1" runId="run-1" catalogSkills={[makeSkill()]} />,
    );

    expect(html).toContain("Analisi fallita");
    expect(html).toContain("Run fallita.");
  });
});
