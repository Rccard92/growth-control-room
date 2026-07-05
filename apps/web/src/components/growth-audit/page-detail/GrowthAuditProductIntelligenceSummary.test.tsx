import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditProductIntelligenceSummary } from "./GrowthAuditProductIntelligenceSummary";

const sampleProductPage: GrowthAuditPage = {
  id: "page-1",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  title: "Miele",
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-1",
  metadata: {
    searchConsole: {
      impressions: 1200,
      ctr: 0.008,
      position: 9.5,
    },
    analytics: {
      sessions: 300,
      conversions: 0,
    },
  },
};

describe("GrowthAuditProductIntelligenceSummary", () => {
  it("renders Product Intelligence and Product Priority Score for product pages", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditProductIntelligenceSummary
        page={sampleProductPage}
        findings={[]}
        tasks={[]}
        priorityActions={[]}
      />,
    );

    expect(html).toContain("Product Intelligence");
    expect(html).toContain("Product Priority Score");
    expect(html).toContain("Priorità economica");
    expect(html).toContain("Economic Priority Score");
    expect(html).toContain('id="product-intelligence"');
  });

  it("renders nothing for non-product pages", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditProductIntelligenceSummary
        page={{
          ...sampleProductPage,
          pageType: "collection",
          sourceEntityType: "shopify_collection",
        }}
        findings={[]}
        tasks={[]}
        priorityActions={[]}
      />,
    );

    expect(html).toBe("");
  });
});
