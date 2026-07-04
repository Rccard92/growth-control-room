import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageWorkspaceHeader } from "./GrowthAuditPageWorkspaceHeader";

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
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-1",
};

describe("GrowthAuditPageWorkspaceHeader", () => {
  it("renders sticky header with scores and main CTAs", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <GrowthAuditPageWorkspaceHeader
          projectId="proj-1"
          page={samplePage}
          findingsCount={2}
          tasksCount={1}
          canRescan
          onScrollToSection={() => {}}
        />
      </MemoryRouter>,
    );

    expect(html).toContain("growth-audit-workspace-header--sticky");
    expect(html).toContain("Torna al Growth Audit");
    expect(html).toContain("Prodotto");
    expect(html).toContain("Score tecnico");
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("Analizza AI/GEO/CRO");
    expect(html).toContain("Riscansiona pagina");
    expect(html).toContain("72");
  });
});
