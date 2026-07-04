import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { GrowthAuditPageTasksPanel } from "./GrowthAuditPageTasksPanel";

describe("GrowthAuditPageTasksPanel", () => {
  it("shows owner and priority labels in Italian", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageTasksPanel
        tasks={[
          {
            id: "t1",
            runId: "run",
            projectId: "proj",
            pageId: "page-1",
            title: "Aggiungere schema Product",
            description: "Implementa JSON-LD Product completo.",
            ownerType: "seo",
            priority: "high",
            estimatedEffort: "medium",
            status: "open",
          },
        ]}
      />,
    );

    expect(html).toContain("Alta");
    expect(html).toContain("SEO");
    expect(html).toContain("Aggiungere schema Product");
    expect(html).toContain("arricchiti con AI/GEO/CRO");
  });

  it("shows empty state without tasks", () => {
    const html = renderToStaticMarkup(<GrowthAuditPageTasksPanel tasks={[]} />);
    expect(html).toContain("Nessun task tecnico aperto per questa pagina.");
  });
});
