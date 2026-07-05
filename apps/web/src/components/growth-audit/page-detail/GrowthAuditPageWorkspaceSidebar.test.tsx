import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageWorkspaceSidebar } from "./GrowthAuditPageWorkspaceSidebar";

const samplePage: GrowthAuditPage = {
  id: "page-2",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  title: "Miele",
  httpStatus: 200,
  score: 72,
  analyzedAt: "2026-06-13T10:00:00Z",
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-1",
  sourceEntityTitle: "Miele Premium",
  sourceEntityHandle: "miele",
};

describe("GrowthAuditPageWorkspaceSidebar", () => {
  it("renders workflow and quick links", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceSidebar
        page={samplePage}
        priorityActionsCount={3}
        openFindingsCount={2}
        openTasksCount={1}
        hasAiResult={false}
        shopifySectionAvailable
        hasShopifyCommerceData
        aiSectionAvailable
        onScrollToSection={() => {}}
      />,
    );

    expect(html).toContain("Workflow consigliato");
    expect(html).toContain("Collegamenti rapidi");
    expect(html).toContain("Product Intelligence");
    expect(html).toContain("Cosa sistemare prima");
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("Shopify Commerce");
    expect(html).toContain("AI/GEO/CRO");
    expect(html).toContain("Dati tecnici");
    expect(html).toContain("trust, CTA, immagini");
  });
});
