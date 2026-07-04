import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { GrowthAuditAiCoveragePanel } from "./GrowthAuditAiCoveragePanel";

describe("GrowthAuditAiCoveragePanel", () => {
  it("renders AI coverage stats", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditAiCoveragePanel
        stats={{
          totalPages: 25,
          technicallyAnalyzedPages: 25,
          aiAnalyzedPages: 3,
          productsWithoutAi: 8,
          collectionsWithoutAi: 2,
          strategicWithoutAi: 10,
          coveragePercent: 12,
        }}
      />,
    );

    expect(html).toContain("Copertura AI/GEO/CRO");
    expect(html).toContain("25");
    expect(html).toContain("Prodotti senza AI");
    expect(html).toContain("lancia AI/GEO/CRO manualmente");
    expect(html).toContain("12% copertura");
  });
});
