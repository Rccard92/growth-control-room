import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageDrawer } from "./GrowthAuditPageDrawer";

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
  metaDescription: "Miele biologico siciliano dal gusto delicato.",
  canonicalUrl: "https://solmielato.it/products/miele",
  h1: "Miele di Limone",
  httpStatus: 200,
  score: 82,
  metadata: {
    technical: {
      schemaTypes: ["Product", "WebPage"],
      imagesTotal: 5,
      imagesMissingAlt: 1,
      linksInternal: 12,
      linksExternal: 2,
      robots: { noindex: false, nofollow: false },
    },
  },
};

describe("GrowthAuditPageDrawer", () => {
  it("renders URL, score and technical fields", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("https://solmielato.it/products/miele");
    expect(html).toContain("82");
    expect(html).toContain("Buona");
    expect(html).toContain("Miele di Limone");
    expect(html).toContain("Miele biologico siciliano dal gusto delicato.");
    expect(html).toContain("https://solmielato.it/products/miele");
    expect(html).toContain("Product, WebPage");
    expect(html).toContain("Riscansiona pagina — in arrivo");
  });

  it("renders empty states when no findings or tasks", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Nessun problema tecnico prioritario rilevato per questa pagina.");
    expect(html).toContain("Nessun task tecnico aperto per questa pagina.");
  });

  it("returns null when closed", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open={false}
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toBe("");
  });
});
