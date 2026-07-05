import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import type { GrowthAuditEconomicPriorityItem } from "../../lib/growth-audit-utils";
import { GrowthAuditEconomicPriorityPanel } from "./GrowthAuditEconomicPriorityPanel";

const sampleItems: GrowthAuditEconomicPriorityItem[] = [
  {
    pageId: "p1",
    url: "https://example.com/products/miele",
    title: "Miele Biologico",
    handle: "miele",
    score: 86,
    level: "high",
    label: "Priorità alta",
    shortReason: "Prodotto già monetizza, ma CTR e CRO sono migliorabili.",
    reasons: [],
    breakdown: {
      businessImpact: 80,
      organicOpportunity: 70,
      trafficAndConversion: 50,
      ecommerceFunnel: 60,
      technicalAndCroRisk: 40,
      stockAndAvailability: 10,
      dataConfidence: 80,
    },
    metrics: {
      sales: 345.6,
      gscImpressions: 3656,
      gscCtr: 0.0055,
      itemViews: 10761,
      purchases: 587,
      stock: 9,
    },
  },
  {
    pageId: "p2",
    url: "https://example.com/products/polline",
    title: "Polline d'Api",
    score: 25,
    level: "monitor",
    label: "Monitoraggio",
    shortReason: "Dati insufficienti per una priorità economica affidabile.",
    reasons: [],
    breakdown: {
      businessImpact: 0,
      organicOpportunity: 0,
      trafficAndConversion: 0,
      ecommerceFunnel: 0,
      technicalAndCroRisk: 0,
      stockAndAvailability: 0,
      dataConfidence: 20,
    },
    metrics: {},
  },
];

describe("GrowthAuditEconomicPriorityPanel", () => {
  it("renders section title and table rows", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <GrowthAuditEconomicPriorityPanel
          projectId="proj-1"
          runId="run-1"
          items={sampleItems}
        />
      </MemoryRouter>,
    );
    expect(html).toContain("Prodotti da migliorare prima");
    expect(html).toContain("Miele Biologico");
    expect(html).toContain("Priorità alta");
    expect(html).toContain("Apri pagina");
  });

  it("renders filter buttons including Con vendite", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <GrowthAuditEconomicPriorityPanel
          projectId="proj-1"
          runId="run-1"
          items={sampleItems}
        />
      </MemoryRouter>,
    );
    expect(html).toContain("Con vendite");
    expect(html).toContain("Dati incompleti");
  });
});
