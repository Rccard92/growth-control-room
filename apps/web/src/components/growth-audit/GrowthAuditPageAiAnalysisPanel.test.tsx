import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageAiAnalysisPanel } from "./GrowthAuditPageAiAnalysisPanel";

const {
  useGrowthAuditPageResultsMock,
  useAnalyzeGrowthAuditPageWithAiMock,
} = vi.hoisted(() => ({
  useGrowthAuditPageResultsMock: vi.fn(),
  useAnalyzeGrowthAuditPageWithAiMock: vi.fn(),
}));

vi.mock("../../hooks/useGrowthAudit", () => ({
  useGrowthAuditPageResults: useGrowthAuditPageResultsMock,
  useAnalyzeGrowthAuditPageWithAi: useAnalyzeGrowthAuditPageWithAiMock,
}));

const samplePage: GrowthAuditPage = {
  id: "page-1",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  score: 82,
  geoScore: 65,
  croScore: 68,
};

function setupMocks(options?: {
  results?: Array<Record<string, unknown>>;
  isPending?: boolean;
}) {
  useGrowthAuditPageResultsMock.mockReturnValue({
    data: options?.results ?? [],
    isLoading: false,
  });
  useAnalyzeGrowthAuditPageWithAiMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: options?.isPending ?? false,
  });
}

describe("GrowthAuditPageAiAnalysisPanel", () => {
  it("renders empty state when no AI results exist", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageAiAnalysisPanel
        projectId="proj-1"
        runId="run-1"
        page={samplePage}
        runStatus="completed"
      />,
    );

    expect(html).toContain("Non hai ancora analizzato questa pagina con AI/GEO/CRO.");
    expect(html).toContain("Analizza questa pagina");
    expect(html).toContain("pagine prioritarie");
  });

  it("renders score grid and findings from latest completed result", () => {
    setupMocks({
      results: [
        {
          id: "result-1",
          status: "completed",
          score: 72,
          summary: "Buona base SEO con margini CRO.",
          completedAt: "2026-06-13T10:00:00Z",
          rawOutput: {
            seoScore: 70,
            geoScore: 65,
            croScore: 68,
            adsReadinessScore: 60,
          },
          findings: [
            {
              category: "geo",
              severity: "high",
              title: "Manca citazione fonte",
              recommendation: "Aggiungi riferimenti verificabili.",
            },
          ],
          tasks: [
            {
              title: "Rafforza trust signals",
              ownerType: "content",
              priority: "high",
            },
          ],
          artifacts: {
            geoChecklist: ["Verifica entità nominate"],
            croChecklist: ["Aggiungi recensioni visibili"],
          },
        },
      ],
    });

    const html = renderToStaticMarkup(
      <GrowthAuditPageAiAnalysisPanel
        projectId="proj-1"
        runId="run-1"
        page={samplePage}
        runStatus="completed"
      />,
    );

    expect(html).toContain("72");
    expect(html).toContain("GEO");
    expect(html).toContain("CRO");
    expect(html).toContain("geo");
    expect(html).toContain("Manca citazione fonte");
    expect(html).toContain("Rafforza trust signals");
    expect(html).toContain("Verifica entità nominate");
  });

  it("shows loading label and disables CTA while mutation is pending", () => {
    setupMocks({ isPending: true });
    const html = renderToStaticMarkup(
      <GrowthAuditPageAiAnalysisPanel
        projectId="proj-1"
        runId="run-1"
        page={samplePage}
        runStatus="completed"
      />,
    );

    expect(html).toContain("Analisi AI in corso…");
    expect(html).toContain("disabled");
  });

  it("shows warning when run is active", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageAiAnalysisPanel
        projectId="proj-1"
        runId="run-1"
        page={samplePage}
        runStatus="analyzing"
      />,
    );

    expect(html).toContain("non è disponibile mentre il run è in corso");
    expect(html).toContain("disabled");
  });
});
