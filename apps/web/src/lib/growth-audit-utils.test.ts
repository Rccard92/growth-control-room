import { describe, expect, it } from "vitest";
import type { GrowthAuditPage } from "@gcr/shared";
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
  getGrowthAuditShopifyEditorMicrocopy,
  getGrowthAuditShopifyLinkBadgeLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditSourceEntityTypeLabel,
  getGrowthAuditStatusLabel,
  isGrowthAuditPageShopifyLinked,
  getInventoryMessage,
  getTasksForPage,
  getTopPriorityFindings,
  sortGrowthAuditFindings,
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
});
