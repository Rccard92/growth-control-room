import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditTask } from "@gcr/shared";
import { GrowthAuditPriorityActionsPanel } from "./GrowthAuditPriorityActionsPanel";

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
  title: "Miele di Limone",
  metaDescription: "Miele biologico siciliano.",
  httpStatus: 200,
  score: 72,
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-1",
  sourceEntityTitle: "Miele",
  sourceEntityHandle: "miele",
  metadata: {
    technical: {
      schemaTypes: ["Product"],
      imagesTotal: 3,
      imagesMissingAlt: 1,
    },
  },
};

const openFinding: GrowthAuditFinding = {
  id: "finding-1",
  runId: "run-1",
  projectId: "proj-1",
  pageId: "page-1",
  category: "seo",
  severity: "high",
  priority: "high",
  title: "Title debole",
  description: "Il title non è ottimizzato.",
  recommendation: "Rafforza il title con keyword e brand.",
  howToValidate: "Verifica il tag title nel sorgente.",
  status: "open",
};

const openTask: GrowthAuditTask = {
  id: "task-1",
  runId: "run-1",
  projectId: "proj-1",
  pageId: "page-1",
  title: "Ottimizza meta description",
  description: "Riscrivi la meta con benefit chiari.",
  ownerType: "seo",
  priority: "medium",
  estimatedEffort: "low",
  status: "open",
};

describe("GrowthAuditPriorityActionsPanel", () => {
  it("renders Cosa sistemare prima with KPI strip", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPriorityActionsPanel
        page={sampleProductPage}
        findings={[openFinding]}
        tasks={[openTask]}
      />,
    );

    expect(html).toContain("Cosa sistemare prima");
    expect(html).toContain("Azioni ordinate per priorità");
    expect(html).toContain("Azioni totali");
    expect(html).toContain("Alta priorità");
    expect(html).toContain("Quick win");
    expect(html).toContain("CRO / Ads");
  });

  it("renders cards with Come risolvere and Dove intervenire", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPriorityActionsPanel
        page={sampleProductPage}
        findings={[openFinding]}
        tasks={[openTask]}
      />,
    );

    expect(html).toContain("Come risolvere");
    expect(html).toContain("Dove intervenire");
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("Responsabile:");
    expect(html).toContain("Sforzo:");
    expect(html).toContain("Rafforza il title con keyword e brand.");
  });

  it("renders empty state when no actions", () => {
    const cleanPage: GrowthAuditPage = {
      ...sampleProductPage,
      title: "Miele biologico siciliano — acquista online con spedizione rapida",
      metaDescription:
        "Miele biologico siciliano di alta qualità, raccolto artigianalmente. Scopri gusto, origine e benefici con spedizione rapida in tutta Italia.",
      h1: "Miele biologico siciliano",
      canonicalUrl: "https://solmielato.it/products/miele",
      metadata: {
        technical: {
          schemaTypes: ["Product", "WebPage"],
          imagesTotal: 2,
          imagesMissingAlt: 0,
          linksInternal: 12,
          linksExternal: 1,
          robots: { noindex: false, nofollow: false },
          openGraph: {
            title: "Miele biologico",
            description: "Miele siciliano",
            image: "https://solmielato.it/miele.jpg",
          },
        },
      },
    };

    const html = renderToStaticMarkup(
      <GrowthAuditPriorityActionsPanel page={cleanPage} findings={[]} tasks={[]} />,
    );

    expect(html).toContain("Nessuna azione prioritaria aperta");
    expect(html).toContain("analisi AI/GEO/CRO");
  });
});
