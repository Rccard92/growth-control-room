import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageImprovementPanel } from "./GrowthAuditPageImprovementPanel";

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
  title: "Miele di Limone",
  metaDescription: "Miele biologico siciliano dal gusto delicato e naturale.",
  canonicalUrl: "https://solmielato.it/products/miele",
  h1: "Miele di Limone",
  httpStatus: 200,
  score: 86,
  metadata: {
    technical: {
      schemaTypes: ["Product", "WebPage"],
      imagesTotal: 5,
      imagesMissingAlt: 0,
      linksInternal: 12,
      linksExternal: 2,
      robots: { noindex: false, nofollow: false },
    },
  },
};

describe("GrowthAuditPageImprovementPanel", () => {
  it("shows headline, summary and Come risolvere / Come verificare blocks", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageImprovementPanel page={samplePage} findings={[]} />,
    );

    expect(html).toContain("Come migliorare questa pagina");
    expect(html).toContain("Score 86/100");
    expect(html).toContain("Buona");
    expect(html).toContain("Gap rispetto a 100: 14 punti");
    expect(html).toContain("Come risolvere");
    expect(html).toContain("Come verificare");
    expect(html).toContain("migliorare su alcuni dettagli");
  });
});
