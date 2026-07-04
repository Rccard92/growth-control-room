import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPriorityDashboard } from "./GrowthAuditPriorityDashboard";

const pages: GrowthAuditPage[] = [
  {
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
    score: 55,
    sourceEntityType: "shopify_product",
    sourceEntityId: "prod-1",
  },
  {
    id: "page-1",
    runId: "run-1",
    projectId: "proj-1",
    url: "https://solmielato.it",
    normalizedUrl: "https://solmielato.it",
    pageType: "homepage",
    source: "seed",
    status: "analyzed",
    priority: "high",
    title: "Home",
    score: 82,
  },
];

describe("GrowthAuditPriorityDashboard", () => {
  it("renders Priorità Growth Audit", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <GrowthAuditPriorityDashboard
          projectId="proj-1"
          runId="run-1"
          pages={pages}
          findings={[
            {
              id: "f1",
              runId: "run-1",
              projectId: "proj-1",
              pageId: "page-2",
              category: "seo",
              severity: "critical",
              priority: "high",
              title: "Title mancante",
              status: "open",
            },
          ]}
          tasks={[]}
          siteScore={78}
        />
      </MemoryRouter>,
    );

    expect(html).toContain("Priorità Growth Audit");
    expect(html).toContain("Top pagine da correggere");
    expect(html).toContain("Problemi ricorrenti");
    expect(html).toContain("Copertura AI/GEO/CRO");
    expect(html).toContain("Gestisci pagina");
  });
});
