import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageKeywordIntelligencePanel } from "./GrowthAuditPageKeywordIntelligencePanel";

const { useDataForSeoUsageMock } = vi.hoisted(() => ({
  useDataForSeoUsageMock: vi.fn(),
}));

vi.mock("../../hooks/useGrowthAudit", () => ({
  useAnalyzeGrowthAuditPageKeywordIntelligence: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("../../hooks/useDataForSeo", () => ({
  useDataForSeoStatus: () => ({
    data: { configured: true, realCallsEnabled: true },
  }),
  useDataForSeoUsage: useDataForSeoUsageMock,
}));

const productPage: GrowthAuditPage = {
  id: "page-1",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/polline",
  normalizedUrl: "https://solmielato.it/products/polline",
  pageType: "product",
  source: "crawl",
  priority: "medium",
  sourceEntityType: "shopify_product",
  status: "analyzed",
  metadata: {
    keywordIntelligence: {
      syncedAt: new Date().toISOString(),
      seedQueries: [{ query: "polline biologico", impressions: 477, ctr: 0.0021, position: 9 }],
      searchVolume: [
        {
          keyword: "polline biologico",
          searchVolume: 140,
          cpc: 0.29,
          competition: "HIGH",
          trend: { direction: "stable" },
        },
      ],
      competitors: [{ domain: "example.it", appearancesCount: 2, bestPosition: 1, keywords: ["polline biologico"] }],
      serp: [
        {
          keyword: "polline biologico",
          topResults: [{ position: 1, domain: "example.it", title: "Polline", url: "https://example.it" }],
          refinementChips: ["Benefici"],
        },
      ],
      cost: { totalUsd: 0.186, searchVolumeUsd: 0.09, keywordIdeasUsd: 0.09, serpUsd: 0.006 },
    },
  },
};

describe("GrowthAuditPageKeywordIntelligencePanel", () => {
  it("shows cost warning and custom select controls", () => {
    useDataForSeoUsageMock.mockReturnValue({
      data: {
        averageCostByOperation: {
          search_volume_batch: 0.09,
          keyword_ideas: 0.09,
          serp: 0.002,
        },
      },
    });
    const html = renderToStaticMarkup(
      <GrowthAuditPageKeywordIntelligencePanel
        projectId="proj-1"
        runId="run-1"
        page={productPage}
      />,
    );
    expect(html).toContain("credito DataForSEO");
    expect(html).toContain("$0.1860");
    expect(html).toContain("costi osservati");
    expect(html).toContain("gcr-select");
    expect(html).toContain("Max seed query");
  });

  it("shows fallback note without observed usage data", () => {
    useDataForSeoUsageMock.mockReturnValue({ data: undefined });
    const html = renderToStaticMarkup(
      <GrowthAuditPageKeywordIntelligencePanel
        projectId="proj-1"
        runId="run-1"
        page={productPage}
      />,
    );
    expect(html).toContain("$0.1860");
    expect(html).toContain("fallback finché non ci sono costi osservati");
  });

  it("renders metadata tables and competitors", () => {
    useDataForSeoUsageMock.mockReturnValue({ data: undefined });
    const html = renderToStaticMarkup(
      <GrowthAuditPageKeywordIntelligencePanel
        projectId="proj-1"
        runId="run-1"
        page={productPage}
      />,
    );
    expect(html).toContain("polline biologico");
    expect(html).toContain("example.it");
    expect(html).toContain("Benefici");
    expect(html).not.toContain('"truncated"');
  });
});
