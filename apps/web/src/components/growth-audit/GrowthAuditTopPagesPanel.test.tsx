import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { GrowthAuditTopPagesPanel } from "./GrowthAuditTopPagesPanel";
import type { GrowthAuditPagePriorityItem } from "../../lib/growth-audit-utils";

const sampleItem: GrowthAuditPagePriorityItem = {
  pageId: "page-2",
  url: "https://solmielato.it/products/miele",
  title: "Miele",
  pageType: "product",
  pageTypeLabel: "Prodotto",
  sourceLabel: "Shopify prodotto",
  score: 55,
  aiScore: null,
  geoScore: null,
  croScore: null,
  adsReadinessScore: null,
  openFindings: 2,
  highPriorityFindings: 1,
  openTasks: 1,
  isShopifyLinked: true,
  sourceEntityType: "shopify_product",
  priorityScore: 72,
  priorityLevel: "critical",
  reasons: ["Score tecnico basso", "Pagina prodotto collegata a Shopify"],
  recommendedNextAction: "Apri la scheda e correggi da Modifica Shopify",
};

describe("GrowthAuditTopPagesPanel", () => {
  it("renders CTA Gestisci pagina with detail route", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <GrowthAuditTopPagesPanel
          projectId="proj-1"
          runId="run-1"
          items={[sampleItem]}
        />
      </MemoryRouter>,
    );

    expect(html).toContain("Gestisci pagina");
    expect(html).toContain("/projects/proj-1/audit/runs/run-1/pages/page-2");
    expect(html).toContain("Score tecnico basso");
  });
});
