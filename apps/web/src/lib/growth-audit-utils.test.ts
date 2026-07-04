import { describe, expect, it } from "vitest";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditTask } from "@gcr/shared";
import {
  aggregatePageInventory,
  filterInventoryPages,
  filterInventoryPagesByScore,
  formatPageFindingsCount,
  getDefaultRootUrl,
  getFindingsForPage,
  getGrowthAuditInventoryFilterLabel,
  getGrowthAuditPageScoreLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTechnicalMetadata,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditScoreBadgeClass,
  getGrowthAuditScoreBand,
  buildGrowthAuditPageImprovementItems,
  buildGrowthAuditPriorityActions,
  getGrowthAuditEffortLabel,
  getGrowthAuditImprovementHeadline,
  getGrowthAuditPriorityActionLabel,
  getGrowthAuditWhereToFix,
  getGrowthAuditShopifyEditorMicrocopy,
  getGrowthAuditShopifyLinkBadgeLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditSourceEntityTypeLabel,
  getGrowthAuditStatusLabel,
  isGrowthAuditPageShopifyLinked,
  getInventoryMessage,
  getTasksForPage,
  getTopPriorityFindings,
  mapGrowthAuditPageToSeoEntity,
  sortGrowthAuditFindings,
  normalizeGrowthAuditPriorityDedupeKey,
} from "./growth-audit-utils";

const samplePages: GrowthAuditPage[] = [
  {
    id: "1",
    runId: "run",
    projectId: "proj",
    url: "https://example.com",
    normalizedUrl: "https://example.com",
    pageType: "homepage",
    source: "seed",
    status: "classified",
    priority: "high",
  },
  {
    id: "2",
    runId: "run",
    projectId: "proj",
    url: "https://example.com/products/a",
    normalizedUrl: "https://example.com/products/a",
    pageType: "product",
    source: "shopify_product",
    status: "classified",
    priority: "normal",
  },
  {
    id: "3",
    runId: "run",
    projectId: "proj",
    url: "https://example.com/blogs/news/post",
    normalizedUrl: "https://example.com/blogs/news/post",
    pageType: "blog_article",
    source: "sitemap",
    status: "classified",
    priority: "normal",
  },
];

describe("growth-audit-utils", () => {
  it("translates run status to Italian", () => {
    expect(getGrowthAuditStatusLabel("completed")).toBe("Completato");
    expect(getGrowthAuditStatusLabel("discovering")).toBe("Discovery in corso");
  });

  it("translates phase to Italian", () => {
    expect(getGrowthAuditPhaseLabel("classification")).toBe("Classificazione");
    expect(getGrowthAuditPhaseLabel("finalization")).toBe("Finalizzazione");
  });

  it("translates page type and source labels", () => {
    expect(getGrowthAuditPageTypeLabel("static_page")).toBe("Pagina statica");
    expect(getGrowthAuditPageTypeLabel("blog_article")).toBe("Articolo blog");
    expect(getGrowthAuditPageSourceLabel("shopify_product")).toBe("Shopify prodotto");
    expect(getGrowthAuditPageSourceLabel("shopify_collection")).toBe("Shopify collezione");
  });

  it("returns readable inventory filter labels", () => {
    expect(getGrowthAuditInventoryFilterLabel("product")).toBe("Prodotti");
    expect(getGrowthAuditInventoryFilterLabel("static_page")).toBe("Statiche");
  });

  it("returns source badge classes", () => {
    expect(getGrowthAuditSourceBadgeClass("seed")).toContain("--seed");
    expect(getGrowthAuditSourceBadgeClass("shopify_product")).toContain("--shopify-product");
    expect(getGrowthAuditSourceBadgeClass("sitemap")).toContain("--sitemap");
  });

  it("returns Shopify source entity type labels", () => {
    expect(getGrowthAuditSourceEntityTypeLabel("shopify_product")).toBe("Prodotto Shopify");
    expect(getGrowthAuditSourceEntityTypeLabel("shopify_collection")).toBe("Collection Shopify");
    expect(getGrowthAuditSourceEntityTypeLabel("shopify_page")).toBe("Pagina Shopify");
    expect(getGrowthAuditSourceEntityTypeLabel("shopify_article")).toBe("Articolo Shopify");
    expect(getGrowthAuditSourceEntityTypeLabel(null)).toBe("Non collegata");
  });

  it("detects Shopify linked pages and editor microcopy", () => {
    const linked: GrowthAuditPage = {
      ...samplePages[1],
      sourceEntityType: "shopify_product",
      sourceEntityHandle: "a",
      sourceEntityTitle: "Product A",
    };
    expect(isGrowthAuditPageShopifyLinked(linked)).toBe(true);
    expect(getGrowthAuditShopifyLinkBadgeLabel(linked)).toBe("Collegata");
    expect(getGrowthAuditShopifyEditorMicrocopy(linked)).toContain("Nel prossimo step");

    const unlinked = samplePages[0];
    expect(isGrowthAuditPageShopifyLinked(unlinked)).toBe(false);
    expect(getGrowthAuditShopifyLinkBadgeLabel(unlinked)).toBe("Non collegata");
    expect(getGrowthAuditShopifyEditorMicrocopy(unlinked)).toBeNull();
  });

  it("aggregates inventory counts", () => {
    const counts = aggregatePageInventory(samplePages);
    expect(counts.total).toBe(3);
    expect(counts.homepage).toBe(1);
    expect(counts.product).toBe(1);
    expect(counts.blog).toBe(1);
    expect(counts.bySource.shopify_product).toBe(1);
  });

  it("filters inventory pages by type", () => {
    const products = filterInventoryPages(samplePages, "product");
    expect(products).toHaveLength(1);
    expect(products[0].pageType).toBe("product");
  });

  it("builds inventory messages", () => {
    expect(getInventoryMessage(3)).toContain("Inventario creato");
    expect(getInventoryMessage(1)).toContain("solo la pagina seed");
    expect(
      getInventoryMessage(3, {
        message: "Technical page scan completed. AI/GEO/CRO analysis is not enabled yet.",
      }),
    ).toContain("Scansione tecnica completata");
  });

  it("builds default root URL from shop domain", () => {
    expect(getDefaultRootUrl("shop.example.com")).toBe("https://shop.example.com");
    expect(getDefaultRootUrl("https://shop.example.com")).toBe("https://shop.example.com");
  });

  it("maps score bands and badge classes", () => {
    expect(getGrowthAuditScoreBand(85)).toBe("good");
    expect(getGrowthAuditScoreBand(70)).toBe("warning");
    expect(getGrowthAuditScoreBand(45)).toBe("critical");
    expect(getGrowthAuditScoreBadgeClass(85)).toContain("--good");
    expect(getGrowthAuditScoreBadgeClass(null)).toContain("--none");
  });

  it("filters inventory pages by score band", () => {
    const pages: GrowthAuditPage[] = [
      { ...samplePages[0], id: "a", score: 90 },
      { ...samplePages[1], id: "b", score: 65 },
      { ...samplePages[2], id: "c", score: 40 },
    ];
    expect(filterInventoryPagesByScore(pages, "good")).toHaveLength(1);
    expect(filterInventoryPagesByScore(pages, "critical")).toHaveLength(1);
  });

  it("orders priority findings by severity", () => {
    const findings = getTopPriorityFindings(
      [
        {
          id: "f1",
          runId: "run",
          projectId: "proj",
          category: "seo",
          severity: "medium",
          priority: "medium",
          title: "Medium",
          status: "open",
        },
        {
          id: "f2",
          runId: "run",
          projectId: "proj",
          category: "seo",
          severity: "critical",
          priority: "high",
          title: "Critical",
          status: "open",
        },
      ],
      2,
    );
    expect(findings[0].severity).toBe("critical");
  });

  it("filters findings and tasks by page id", () => {
    const findings = [
      {
        id: "f1",
        runId: "run",
        projectId: "proj",
        pageId: "page-1",
        category: "seo",
        severity: "high",
        priority: "high",
        title: "A",
        status: "open",
      },
      {
        id: "f2",
        runId: "run",
        projectId: "proj",
        pageId: "page-2",
        category: "seo",
        severity: "low",
        priority: "low",
        title: "B",
        status: "open",
      },
    ];
    const tasks = [
      {
        id: "t1",
        runId: "run",
        projectId: "proj",
        pageId: "page-1",
        title: "Task A",
        ownerType: "seo",
        priority: "high",
        estimatedEffort: "low",
        status: "open",
      },
      {
        id: "t2",
        runId: "run",
        projectId: "proj",
        pageId: "page-2",
        title: "Task B",
        ownerType: "dev",
        priority: "medium",
        estimatedEffort: "medium",
        status: "open",
      },
    ];

    expect(getFindingsForPage(findings, "page-1")).toHaveLength(1);
    expect(getTasksForPage(tasks, "page-1")).toHaveLength(1);
    expect(getFindingsForPage(findings, null)).toHaveLength(0);
  });

  it("sorts findings by severity", () => {
    const sorted = sortGrowthAuditFindings([
      {
        id: "f1",
        runId: "run",
        projectId: "proj",
        category: "seo",
        severity: "info",
        priority: "low",
        title: "Info",
        status: "open",
      },
      {
        id: "f2",
        runId: "run",
        projectId: "proj",
        category: "seo",
        severity: "critical",
        priority: "high",
        title: "Critical",
        status: "open",
      },
    ]);
    expect(sorted[0].severity).toBe("critical");
  });

  it("reads technical metadata safely when metadata is null", () => {
    const meta = getGrowthAuditPageTechnicalMetadata({
      ...samplePages[0],
      metadata: null,
    });
    expect(meta.schemaTypes).toEqual([]);
    expect(meta.imagesTotal).toBeNull();
    expect(meta.robots).toBeNull();
  });

  it("maps score labels and findings count", () => {
    expect(getGrowthAuditPageScoreLabel(82)).toBe("Buona");
    expect(getGrowthAuditPageScoreLabel(67)).toBe("Da migliorare");
    expect(getGrowthAuditPageScoreLabel(43)).toBe("Critica");
    expect(getGrowthAuditPageScoreLabel(null)).toBe("Non disponibile");
    expect(formatPageFindingsCount(0)).toBe("Nessun problema");
    expect(formatPageFindingsCount(1)).toBe("1 problema");
    expect(formatPageFindingsCount(2)).toBe("2 problemi");
  });

  it("buildGrowthAuditPageImprovementItems returns items even with empty findings", () => {
    const page: GrowthAuditPage = {
      id: "page-1",
      runId: "run",
      projectId: "proj",
      url: "https://example.com/products/a",
      normalizedUrl: "https://example.com/products/a",
      pageType: "product",
      source: "shopify_product",
      status: "analyzed",
      priority: "normal",
      title: "Prodotto test",
      metaDescription: "Descrizione meta abbastanza lunga per superare la soglia minima consigliata.",
      h1: "Prodotto test",
      httpStatus: 200,
      score: 86,
      canonicalUrl: "https://example.com/products/a",
      metadata: {
        technical: {
          schemaTypes: ["WebPage"],
          imagesTotal: 3,
          imagesMissingAlt: 2,
          linksInternal: 5,
          linksExternal: 1,
          robots: { noindex: false, nofollow: false },
        },
      },
    };

    const items = buildGrowthAuditPageImprovementItems(page, []);
    expect(items.length).toBeGreaterThan(0);
    expect(items.some((item) => item.key === "http")).toBe(true);
    expect(items.find((item) => item.key === "productSchema")?.status).toBe("warning");
    expect(items.find((item) => item.key === "imagesAlt")?.status).toBe("warning");
  });

  it("getGrowthAuditImprovementHeadline reports Buona and gap 14 for score 86", () => {
    const headline = getGrowthAuditImprovementHeadline({
      ...samplePages[1],
      score: 86,
    });
    expect(headline.label).toBe("Buona");
    expect(headline.gap).toBe(14);
    expect(headline.text).toContain("86/100");
    expect(headline.text).toContain("14 punti");
  });

  it("mapGrowthAuditPageToSeoEntity maps linked product and collection", () => {
    expect(
      mapGrowthAuditPageToSeoEntity({
        ...samplePages[1],
        sourceEntityType: "shopify_product",
        sourceEntityId: "prod-99",
      }),
    ).toEqual({ entityType: "product", entityId: "prod-99" });

    expect(
      mapGrowthAuditPageToSeoEntity({
        ...samplePages[0],
        pageType: "collection",
        sourceEntityType: "shopify_collection",
        sourceEntityId: "col-12",
      }),
    ).toEqual({ entityType: "collection", entityId: "col-12" });

    expect(
      mapGrowthAuditPageToSeoEntity({
        ...samplePages[0],
        sourceEntityType: "shopify_page",
        sourceEntityId: "page-1",
      }),
    ).toBeNull();
  });

  describe("buildGrowthAuditPriorityActions", () => {
    const productPage: GrowthAuditPage = {
      id: "page-prod",
      runId: "run-1",
      projectId: "proj-1",
      url: "https://example.com/products/a",
      normalizedUrl: "https://example.com/products/a",
      pageType: "product",
      source: "shopify_product",
      status: "analyzed",
      priority: "normal",
      sourceEntityType: "shopify_product",
      sourceEntityId: "prod-1",
    };

    const baseFinding = (
      overrides: Partial<GrowthAuditFinding> & Pick<GrowthAuditFinding, "id" | "title" | "severity">,
    ): GrowthAuditFinding => ({
      runId: "run-1",
      projectId: "proj-1",
      pageId: "page-prod",
      category: "seo",
      priority: "high",
      status: "open",
      recommendation: "Fix consigliato",
      ...overrides,
    });

    const baseTask = (
      overrides: Partial<GrowthAuditTask> & Pick<GrowthAuditTask, "id" | "title">,
    ): GrowthAuditTask => ({
      runId: "run-1",
      projectId: "proj-1",
      pageId: "page-prod",
      ownerType: "seo",
      priority: "medium",
      estimatedEffort: "low",
      status: "open",
      ...overrides,
    });

    it("maps open finding to action with source finding", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [baseFinding({ id: "f1", title: "Title debole", severity: "high" })],
        tasks: [],
        improvementItems: [],
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].source).toBe("finding");
      expect(actions[0].priority).toBe("high");
    });

    it("maps open task to action", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [],
        tasks: [baseTask({ id: "t1", title: "Aggiorna meta" })],
        improvementItems: [],
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].source).toBe("task");
    });

    it("ignores completed and superseded tasks", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [],
        tasks: [
          baseTask({ id: "t1", title: "Fatto", status: "completed" }),
          baseTask({ id: "t2", title: "Sostituito", status: "superseded" }),
        ],
        improvementItems: [],
      });
      expect(actions).toHaveLength(0);
    });

    it("includes improvement warnings", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [],
        tasks: [],
        improvementItems: [
          {
            key: "imagesAlt",
            label: "images",
            status: "warning",
            title: "Alt immagini",
            description: "Mancano alt.",
            recommendation: "Aggiungi alt descrittivi.",
            howToValidate: "Controlla le immagini.",
          },
        ],
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].source).toBe("improvement");
      expect(actions[0].priority).toBe("medium");
    });

    it("deduplicates similar titles across sources", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [
          baseFinding({
            id: "f1",
            title: "Title debole",
            severity: "high",
            recommendation: "Migliora il title",
          }),
          baseFinding({
            id: "f2",
            title: "Title debole",
            severity: "medium",
            recommendation: "Migliora il title",
          }),
        ],
        tasks: [],
        improvementItems: [],
      });
      expect(actions).toHaveLength(1);
      expect(actions[0].source).toBe("finding");
      expect(actions[0].priority).toBe("high");
    });

    it("orders critical before high before medium", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [
          baseFinding({ id: "f1", title: "Medio", severity: "medium" }),
          baseFinding({ id: "f2", title: "Critico", severity: "critical" }),
          baseFinding({ id: "f3", title: "Alto", severity: "high" }),
        ],
        tasks: [],
        improvementItems: [],
      });
      expect(actions.map((action) => action.priority)).toEqual(["critical", "high", "medium"]);
    });

    it("prioritizes CRO/Ads on product pages at same priority", () => {
      const actions = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [
          baseFinding({ id: "f1", title: "SEO issue", severity: "high", category: "seo" }),
          baseFinding({
            id: "f2",
            title: "CTA debole",
            severity: "high",
            category: "cro",
            recommendation: "Rafforza CTA",
          }),
        ],
        tasks: [],
        improvementItems: [],
      });
      expect(actions[0].category).toBe("cro");
      expect(actions[1].category).toBe("seo");
    });

    it("getGrowthAuditWhereToFix maps title and schema cases", () => {
      const titleAction = buildGrowthAuditPriorityActions({
        page: productPage,
        findings: [
          baseFinding({
            id: "f1",
            title: "Meta description mancante",
            severity: "high",
            category: "seo",
          }),
        ],
        tasks: [],
        improvementItems: [],
      })[0];

      expect(getGrowthAuditWhereToFix(titleAction, productPage)).toContain("Shopify");

      const schemaAction = {
        id: "schema-1",
        source: "finding" as const,
        category: "schema" as const,
        priority: "medium" as const,
        ownerType: "dev" as const,
        effort: "medium" as const,
        title: "Schema incompleto",
        description: "",
        recommendation: "Aggiungi Product schema",
      };
      expect(getGrowthAuditWhereToFix(schemaAction, productPage)).toContain("Tema Shopify");
    });

    it("normalizeGrowthAuditPriorityDedupeKey normalizes case and accents", () => {
      const keyA = normalizeGrowthAuditPriorityDedupeKey({
        title: "Title Debole",
        category: "seo",
        recommendation: "Migliora il Title",
      });
      const keyB = normalizeGrowthAuditPriorityDedupeKey({
        title: "title debole",
        category: "seo",
        recommendation: "migliora il title",
      });
      expect(keyA).toBe(keyB);
    });

    it("getGrowthAuditPriorityActionLabel returns Italian labels", () => {
      expect(getGrowthAuditPriorityActionLabel("critical")).toBe("Critico");
      expect(getGrowthAuditEffortLabel("low")).toBe("Basso");
    });
  });
});
