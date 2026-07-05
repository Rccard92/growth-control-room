import { describe, expect, it } from "vitest";
import type { GrowthAuditFinding, GrowthAuditPage, GrowthAuditTask } from "@gcr/shared";
import {
  aggregatePageInventory,
  filterInventoryPages,
  filterInventoryPagesByScore,
  formatPageFindingsCount,
  getDefaultRootUrl,
  getGrowthAuditDashboardKpiItems,
  computeGrowthAuditPageScoreAverages,
  isMyshopifyDomain,
  getGrowthAuditPublicDomainDisplay,
  formatGrowthAuditPublicSiteHostname,
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
  buildGrowthAuditPagePriorityItems,
  buildGrowthAuditSiteIssueClusters,
  buildGrowthAuditAiCoverageStats,
  buildGrowthAuditPageWorkflowSteps,
  buildGrowthAuditProductIntelligenceSummary,
  buildGrowthAuditEconomicPriorityItem,
  buildGrowthAuditEconomicPriorityRanking,
  filterGrowthAuditEconomicPriorityItems,
  getGrowthAuditPriorityLevelLabel,
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

  it("detects myshopify admin domains", () => {
    expect(isMyshopifyDomain("solmielato.myshopify.com")).toBe(true);
    expect(isMyshopifyDomain("https://solmielato.myshopify.com")).toBe(true);
    expect(isMyshopifyDomain("https://solmielato.it")).toBe(false);
  });

  it("builds default root URL from public run URL, ignoring myshopify", () => {
    expect(
      getDefaultRootUrl({
        projectPublicSiteUrl: "https://solmielato.it",
        activeRun: { rootUrl: "https://example.com" },
      }),
    ).toBe("https://solmielato.it");
    expect(
      getDefaultRootUrl({
        activeRun: { rootUrl: "https://solmielato.it" },
        latestRun: { rootUrl: "https://solmielato.myshopify.com" },
      }),
    ).toBe("https://solmielato.it");
    expect(
      getDefaultRootUrl({
        latestRun: { rootUrl: "solmielato.myshopify.com" },
      }),
    ).toBe("");
    expect(
      getDefaultRootUrl({
        rootUrlOverride: "https://shop.example.com",
      }),
    ).toBe("https://shop.example.com");
  });

  it("returns public domain display label with project priority", () => {
    expect(
      getGrowthAuditPublicDomainDisplay(
        { publicSiteUrl: "https://solmielato.it" },
        { rootUrl: "https://example.com" },
      ),
    ).toBe("https://solmielato.it");
    expect(getGrowthAuditPublicDomainDisplay({ publicSiteUrl: "https://solmielato.it" })).toBe(
      "https://solmielato.it",
    );
    expect(getGrowthAuditPublicDomainDisplay(null, { rootUrl: "solmielato.myshopify.com" })).toBe(
      "Dominio pubblico non configurato",
    );
  });

  it("formats public site hostname for dashboard hero", () => {
    expect(formatGrowthAuditPublicSiteHostname("https://solmielato.it/")).toBe("solmielato.it");
    expect(formatGrowthAuditPublicSiteHostname("solmielato.myshopify.com")).toBeNull();
  });

  it("computes dashboard KPI averages from page AI metadata", () => {
    const pages: GrowthAuditPage[] = [
      {
        ...samplePages[0],
        metadata: {
          ai: { geoScore: 80, croScore: 70, adsReadinessScore: 60 },
        },
      },
      {
        ...samplePages[1],
        geoScore: 60,
        croScore: 50,
      },
    ];
    const averages = computeGrowthAuditPageScoreAverages(pages);
    expect(averages.geoAverage).toBe(70);
    expect(averages.croAverage).toBe(60);
    expect(averages.adsAverage).toBe(60);

    const kpis = getGrowthAuditDashboardKpiItems(
      {
        siteScore: 78,
        pagesAnalyzed: 3,
        summary: { pagesAnalyzed: 3, criticalFindings: 1, highFindings: 2, tasksOpen: 2 },
      },
      pages,
    );
    expect(kpis.find((kpi) => kpi.label === "Score tecnico")?.value).toBe("78");
    expect(kpis.find((kpi) => kpi.label === "GEO medio")?.value).toBe("70");
    expect(kpis.find((kpi) => kpi.label === "Performance")?.meta).toBe("Non analizzato");
  });

  it("uses averagePerformanceScore for dashboard KPI when present", () => {
    const kpis = getGrowthAuditDashboardKpiItems(
      {
        siteScore: 78,
        pagesAnalyzed: 3,
        performanceScore: 55,
        summary: {
          pagesAnalyzed: 3,
          averagePerformanceScore: 72,
        },
      },
      samplePages,
    );
    expect(kpis.find((kpi) => kpi.label === "Performance")?.value).toBe("72");
    expect(kpis.find((kpi) => kpi.label === "Performance")?.meta).toBeUndefined();
  });

  it("includes Search Console KPIs from run summary", () => {
    const kpis = getGrowthAuditDashboardKpiItems(
      {
        siteScore: 78,
        pagesAnalyzed: 3,
        summary: {
          pagesAnalyzed: 3,
          searchConsole: {
            totalClicks: 120,
            totalImpressions: 5400,
            averageCtr: 0.0222,
            averagePosition: 9.3,
            pagesWithData: 4,
            opportunityPages: 2,
            lastSyncedAt: "2026-06-13T10:00:00Z",
          },
        },
      },
      samplePages,
    );
    expect(kpis.find((kpi) => kpi.label === "Click organici")?.value).toBe("120");
    expect(kpis.find((kpi) => kpi.label === "Impression")?.value).toBe("5400");
    expect(kpis.find((kpi) => kpi.label === "CTR medio")?.value).toBe("2.22%");
    expect(kpis.find((kpi) => kpi.label === "Posizione media")?.value).toBe("9.3");
    expect(kpis.find((kpi) => kpi.label === "Pagine con dati GSC")?.value).toBe("4");
  });

  it("includes GA4 KPIs from run summary", () => {
    const kpis = getGrowthAuditDashboardKpiItems(
      {
        siteScore: 78,
        pagesAnalyzed: 3,
        summary: {
          pagesAnalyzed: 3,
          analytics: {
            totalSessions: 320,
            totalUsers: 250,
            averageEngagementRate: 0.415,
            totalConversions: 12,
            totalRevenue: 1540.5,
            pagesWithData: 6,
            lowEngagementPages: 2,
            highTrafficLowConversionPages: 1,
            lastSyncedAt: "2026-06-13T10:00:00Z",
          },
        },
      },
      samplePages,
    );
    expect(kpis.find((kpi) => kpi.label === "Sessioni")?.value).toBe("320");
    expect(kpis.find((kpi) => kpi.label === "Utenti")?.value).toBe("250");
    expect(kpis.find((kpi) => kpi.label === "Engagement rate medio")?.value).toBe("41.50%");
    expect(kpis.find((kpi) => kpi.label === "Conversioni")?.value).toBe("12");
    expect(kpis.find((kpi) => kpi.label === "Revenue")?.value).toBe("1540.50");
    expect(kpis.find((kpi) => kpi.label === "Pagine con dati GA4")?.value).toBe("6");
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

  describe("buildGrowthAuditPagePriorityItems", () => {
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
      score: 55,
      sourceEntityType: "shopify_product",
      sourceEntityId: "prod-1",
    };

    const staticPage: GrowthAuditPage = {
      id: "page-static",
      runId: "run-1",
      projectId: "proj-1",
      url: "https://example.com/pages/about",
      normalizedUrl: "https://example.com/pages/about",
      pageType: "static_page",
      source: "sitemap",
      status: "analyzed",
      priority: "normal",
      score: 88,
    };

    it("orders by priorityScore desc", () => {
      const items = buildGrowthAuditPagePriorityItems({
        pages: [staticPage, productPage],
        findings: [
          {
            id: "f1",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "page-prod",
            category: "seo",
            severity: "high",
            priority: "high",
            title: "Title debole",
            status: "open",
          },
          {
            id: "f2",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "page-static",
            category: "seo",
            severity: "low",
            priority: "low",
            title: "Dettaglio minore",
            status: "open",
          },
        ],
        tasks: [],
      });
      expect(items[0].pageId).toBe("page-prod");
      expect(items[0].priorityScore).toBeGreaterThan(items[1].priorityScore);
    });

    it("product with high finding ranks above static page with low", () => {
      const items = buildGrowthAuditPagePriorityItems({
        pages: [staticPage, productPage],
        findings: [
          {
            id: "f1",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "page-prod",
            category: "seo",
            severity: "high",
            priority: "high",
            title: "Title debole",
            status: "open",
          },
        ],
        tasks: [],
      });
      expect(items[0].pageType).toBe("product");
    });

    it("adds AI analysis reason for strategic pages without AI", () => {
      const items = buildGrowthAuditPagePriorityItems({
        pages: [productPage],
        findings: [],
        tasks: [],
      });
      expect(items[0].reasons).toContain("Non ancora analizzata con AI/GEO/CRO");
    });

    it("adds Shopify linked reason for product", () => {
      const items = buildGrowthAuditPagePriorityItems({
        pages: [productPage],
        findings: [],
        tasks: [],
      });
      expect(items[0].reasons).toContain("Pagina prodotto collegata a Shopify");
      expect(items[0].isShopifyLinked).toBe(true);
    });

    it("adds performance reason for strategic pages without performance analysis", () => {
      const items = buildGrowthAuditPagePriorityItems({
        pages: [productPage],
        findings: [],
        tasks: [],
      });
      expect(items[0].reasons).toContain("Performance non ancora analizzata");
    });

    it("adds Search Console CTR opportunity reason when metadata indicates low CTR", () => {
      const pageWithGsc: GrowthAuditPage = {
        ...staticPage,
        metadata: {
          searchConsole: {
            clicks: 2,
            impressions: 250,
            ctr: 0.008,
            position: 11,
            topQueries: [{ query: "miele", clicks: 1, impressions: 80, ctr: 0.0125, position: 9 }],
          },
        },
      };
      const items = buildGrowthAuditPagePriorityItems({
        pages: [pageWithGsc],
        findings: [],
        tasks: [],
      });
      expect(items[0].reasons).toContain("Opportunità CTR da Search Console");
      expect(items[0].reasons).toContain("Query reali disponibili");
    });

    it("adds GA4 no-conversion reason for product with sessions", () => {
      const pageWithGa4: GrowthAuditPage = {
        ...productPage,
        score: 75,
        metadata: {
          analytics: {
            sessions: 45,
            totalUsers: 40,
            engagedSessions: 15,
            engagementRate: 0.33,
            averageSessionDuration: 70,
            conversions: 0,
            revenue: 0,
            source: "ga4",
            periodDays: 28,
          },
        },
      };
      const items = buildGrowthAuditPagePriorityItems({
        pages: [pageWithGa4],
        findings: [],
        tasks: [],
      });
      expect(items[0].reasons).toContain("Traffico GA4 senza conversioni");
    });

    it("getGrowthAuditPriorityLevelLabel returns Italian labels", () => {
      expect(getGrowthAuditPriorityLevelLabel("critical")).toBe("Critico");
      expect(getGrowthAuditPriorityLevelLabel("high")).toBe("Alto");
    });
  });

  describe("buildGrowthAuditSiteIssueClusters", () => {
    it("groups similar open findings", () => {
      const clusters = buildGrowthAuditSiteIssueClusters(
        [
          {
            id: "f1",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "p1",
            category: "images",
            severity: "high",
            priority: "high",
            title: "Immagini senza alt",
            recommendation: "Aggiungi alt descrittivi.",
            status: "open",
          },
          {
            id: "f2",
            runId: "run-1",
            projectId: "proj-1",
            pageId: "p2",
            category: "images",
            severity: "medium",
            priority: "medium",
            title: "Immagini senza alt",
            recommendation: "Aggiungi alt descrittivi.",
            status: "open",
          },
        ],
        [],
      );
      expect(clusters).toHaveLength(1);
      expect(clusters[0].count).toBe(2);
      expect(clusters[0].title).toBe("Immagini senza alt");
      expect(clusters[0].affectedPageIds).toEqual(["p1", "p2"]);
    });
  });

  describe("buildGrowthAuditAiCoverageStats", () => {
    it("counts strategic pages without AI", () => {
      const stats = buildGrowthAuditAiCoverageStats([
        {
          id: "p1",
          runId: "run-1",
          projectId: "proj-1",
          url: "https://example.com/products/a",
          normalizedUrl: "https://example.com/products/a",
          pageType: "product",
          source: "shopify_product",
          status: "analyzed",
          priority: "normal",
        },
        {
          id: "p2",
          runId: "run-1",
          projectId: "proj-1",
          url: "https://example.com",
          normalizedUrl: "https://example.com",
          pageType: "homepage",
          source: "seed",
          status: "analyzed",
          priority: "high",
          metadata: {
            ai: { analyzedAt: "2026-06-13T10:00:00Z", latestScore: 82 },
          },
        },
      ]);
      expect(stats.productsWithoutAi).toBe(1);
      expect(stats.strategicWithoutAi).toBe(1);
      expect(stats.aiAnalyzedPages).toBe(1);
    });
  });

  describe("buildGrowthAuditPageWorkflowSteps", () => {
    it("marks AI step done when result exists", () => {
      const steps = buildGrowthAuditPageWorkflowSteps({
        page: {
          id: "p1",
          runId: "run",
          projectId: "proj",
          url: "https://example.com/products/a",
          normalizedUrl: "https://example.com/products/a",
          pageType: "product",
          source: "shopify_product",
          status: "analyzed",
          priority: "normal",
          score: 70,
        },
        priorityActionsCount: 2,
        hasAiResult: true,
        shopifyEditable: true,
        openFindingsCount: 1,
      });
      const aiStep = steps.find((step) => step.key === "ai");
      expect(aiStep?.status).toBe("done");
    });

    it("marks modify step available for Shopify product", () => {
      const steps = buildGrowthAuditPageWorkflowSteps({
        page: {
          id: "p1",
          runId: "run",
          projectId: "proj",
          url: "https://example.com/products/a",
          normalizedUrl: "https://example.com/products/a",
          pageType: "product",
          source: "shopify_product",
          status: "analyzed",
          priority: "normal",
        },
        priorityActionsCount: 0,
        hasAiResult: false,
        shopifyEditable: true,
        openFindingsCount: 0,
      });
      const editStep = steps.find((step) => step.key === "edit");
      expect(editStep?.status).toBe("available");
    });

    it("marks performance step done when result exists", () => {
      const steps = buildGrowthAuditPageWorkflowSteps({
        page: {
          id: "p1",
          runId: "run",
          projectId: "proj",
          url: "https://example.com/products/a",
          normalizedUrl: "https://example.com/products/a",
          pageType: "product",
          source: "shopify_product",
          status: "analyzed",
          priority: "normal",
        },
        priorityActionsCount: 0,
        hasAiResult: false,
        hasPerformanceResult: true,
        shopifyEditable: true,
        openFindingsCount: 0,
      });
      const performanceStep = steps.find((step) => step.key === "performance");
      expect(performanceStep?.status).toBe("done");
      expect(performanceStep?.anchorId).toBe("performance");
    });

    it("points product workflow priority step to product-intelligence", () => {
      const steps = buildGrowthAuditPageWorkflowSteps({
        page: {
          id: "p1",
          runId: "run",
          projectId: "proj",
          url: "https://example.com/products/a",
          normalizedUrl: "https://example.com/products/a",
          pageType: "product",
          source: "shopify_product",
          status: "analyzed",
          priority: "normal",
          sourceEntityType: "shopify_product",
        },
        priorityActionsCount: 1,
        hasAiResult: false,
        shopifyEditable: true,
        openFindingsCount: 0,
      });
      const priorityStep = steps.find((step) => step.key === "priority");
      expect(priorityStep?.label).toBe("Valuta priorità");
      expect(priorityStep?.anchorId).toBe("product-intelligence");
    });
  });

  describe("buildGrowthAuditProductIntelligenceSummary", () => {
    const baseProductPage: GrowthAuditPage = {
      id: "p1",
      runId: "run",
      projectId: "proj",
      url: "https://example.com/products/a",
      normalizedUrl: "https://example.com/products/a",
      pageType: "product",
      source: "shopify_product",
      status: "analyzed",
      priority: "normal",
      sourceEntityType: "shopify_product",
      sourceEntityId: "prod-1",
    };

    it("returns available=false for non product pages", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          pageType: "collection",
          sourceEntityType: "shopify_collection",
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.available).toBe(false);
    });

    it("generates high/critical priority for high GSC impressions and low CTR", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            searchConsole: {
              impressions: 1500,
              ctr: 0.005,
              position: 11,
              topQueries: [{ query: "miele bio" }],
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.available).toBe(true);
      expect(summary.score).toBeGreaterThanOrEqual(60);
      expect(["high", "critical"]).toContain(summary.level);
      expect(summary.title).toContain("visibilità organica");
    });

    it("generates CRO action for high GA4 sessions and zero conversions", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            analytics: {
              sessions: 420,
              conversions: 0,
              engagementRate: 0.35,
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.recommendedActions.some((action) => action.title.includes("trust, CTA"))).toBe(
        true,
      );
      expect(summary.title).toContain("traffico");
    });

    it("generates performance action for low performance score", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          performanceScore: 42,
          metadata: {
            performance: {
              latestScore: 42,
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Ottimizza immagini"),
        ),
      ).toBe(true);
    });

    it("lists missing Search Console, GA4, Performance and AI when absent", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: baseProductPage,
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.missingData).toContain("Search Console");
      expect(summary.missingData).toContain("GA4");
      expect(summary.missingData).toContain("Performance");
      expect(summary.missingData).toContain("AI/GEO/CRO");
    });

    it("does not invent revenue when analytics revenue is absent", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            analytics: {
              sessions: 120,
              conversions: 2,
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.evidence.some((signal) => signal.key === "ga4-revenue")).toBe(false);
      const withoutRevenue = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            analytics: { sessions: 400, conversions: 0 },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      const withRevenue = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            analytics: { sessions: 400, conversions: 0, revenue: 150 },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(withRevenue.score).toBeGreaterThan(withoutRevenue.score);
    });

    it("boosts score and evidence when Shopify commerce data is present", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            shopifyCommerce: {
              periodDays: 30,
              sales: 250,
              quantitySold: 15,
              ordersCount: 10,
              currency: "EUR",
              stock: 0,
              availableForSale: false,
              syncedAt: "2026-06-13T10:00:00Z",
            },
            searchConsole: {
              impressions: 500,
              ctr: 0.03,
              position: 8,
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
        runSummary: {
          shopifyCommerce: {
            periodDays: 30,
            totalSales: 1000,
            totalQuantitySold: 50,
            productsWithSales: 3,
            productsWithoutSales: 1,
            productsOutOfStock: 1,
            currency: "EUR",
            topProducts: [],
            lastSyncedAt: "2026-06-13T10:00:00Z",
          },
        },
      });

      expect(summary.evidence.some((signal) => signal.key === "shopify-revenue")).toBe(true);
      expect(summary.evidence.some((signal) => signal.key === "shopify-quantity")).toBe(true);
      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("disponibilità"),
        ),
      ).toBe(true);
    });

    it("suggests monetization action for traffic without Shopify sales", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            shopifyCommerce: {
              periodDays: 30,
              sales: 0,
              quantitySold: 0,
              ordersCount: 0,
              syncedAt: "2026-06-13T10:00:00Z",
            },
            searchConsole: {
              impressions: 800,
              ctr: 0.02,
              position: 9,
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Trasforma traffico in vendite"),
        ),
      ).toBe(true);
      expect(summary.missingData).not.toContain("Shopify Commerce");
    });

    it("boosts score and evidence when GA4 ecommerce funnel data is present", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 120,
              itemsAddedToCart: 0,
              itemsCheckedOut: 0,
              itemsPurchased: 0,
              itemRevenue: 0,
              viewToCartRate: 0,
              cartToPurchaseRate: 0,
              matchedBy: "item_id",
              syncedAt: "2026-06-13T10:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      expect(summary.evidence.some((signal) => signal.key === "ga4-item-views")).toBe(true);
      expect(summary.evidence.some((signal) => signal.key === "ga4-add-to-cart")).toBe(true);
      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Migliora offerta, immagini e CTA"),
        ),
      ).toBe(true);
    });

    it("generates cart friction action for GA4 add to cart without purchase", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 60,
              itemsAddedToCart: 12,
              itemsCheckedOut: 0,
              itemsPurchased: 0,
              itemRevenue: 0,
              matchedBy: "item_id",
              syncedAt: "2026-06-13T10:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Analizza frizione tra carrello e acquisto"),
        ),
      ).toBe(true);
    });

    it("does not use candidateItems for product intelligence score", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 0,
              itemsAddedToCart: 0,
              itemsPurchased: 0,
              itemRevenue: 0,
              matchedBy: "none",
              matchDebug: {
                shopifyKeys: {
                  productGid: "gid://shopify/Product/1",
                  productLegacyId: "1",
                  variantLegacyIds: [],
                  skus: [],
                  titleNormalized: "miele",
                  handleNormalized: "miele",
                },
                matchedBy: "none",
                matchStatus: "no_reliable_match",
                reason: "Nessuna riga GA4 match.",
                candidateItems: [
                  {
                    itemId: "999",
                    itemName: "Miele Bio",
                    itemsViewed: 200,
                    itemsPurchased: 5,
                    itemRevenue: 99,
                    candidateReason: "Nome simile ma non identico.",
                  },
                ],
              },
              syncedAt: "2026-06-13T10:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      expect(summary.evidence.some((signal) => signal.key === "ga4-item-views")).toBe(false);
      const purchaseSignal = summary.evidence.find((signal) => signal.key === "ga4-purchase");
      if (purchaseSignal) {
        expect(purchaseSignal.value).toBe("0");
      }
      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Verifica tracciamento ecommerce GA4"),
        ),
      ).toBe(true);
    });

    it("updates GA4 tracking action copy when product has traffic signals", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            searchConsole: { impressions: 500, ctr: 0.03, position: 8 },
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 0,
              matchedBy: "none",
              syncedAt: "2026-06-13T10:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      const action = summary.recommendedActions.find((item) =>
        item.title.includes("Verifica tracciamento ecommerce GA4"),
      );
      expect(action?.reason).toContain("funnel item-level non è stato abbinato");
      expect(action?.howToValidate).toContain("Shopify → GA4");
    });

    it("uses matched variant breakdown for GA4 evidence and actions", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: {
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 100,
              itemsAddedToCart: 10,
              itemsPurchased: 2,
              itemRevenue: 100,
              matchedBy: "shopify_composite_item_id",
              bestVariantByRevenue: "v1",
              bestVariantByPurchase: "v1",
              variantBreakdown: [
                {
                  variantLegacyId: "v1",
                  variantTitle: "120g",
                  itemViews: 100,
                  itemsAddedToCart: 10,
                  itemsPurchased: 2,
                  itemRevenue: 100,
                  matchedBy: "shopify_composite_item_id",
                },
                {
                  variantLegacyId: "v2",
                  variantTitle: "250g",
                  itemViews: 0,
                  itemsAddedToCart: 0,
                  itemsPurchased: 0,
                  itemRevenue: 0,
                  matchedBy: "none",
                },
              ],
              syncedAt: "2026-06-13T10:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
        priorityActions: [],
      });

      expect(
        summary.evidence.some((signal) => signal.key === "ga4-variants-with-funnel"),
      ).toBe(true);
      expect(
        summary.evidence.some((signal) => signal.key === "ga4-best-variant-revenue"),
      ).toBe(true);
      expect(
        summary.recommendedActions.some((action) =>
          action.title.includes("Ottimizza la variante più redditizia"),
        ),
      ).toBe(true);
    });

    it("includes GA4 Ecommerce Funnel in missingData when absent", () => {
      const summary = buildGrowthAuditProductIntelligenceSummary({
        page: baseProductPage,
        findings: [],
        tasks: [],
        priorityActions: [],
      });
      expect(summary.missingData).toContain("GA4 Ecommerce Funnel");
    });
  });

  describe("buildGrowthAuditEconomicPriorityItem/Ranking", () => {
    const baseProductPage: GrowthAuditPage = {
      id: "p1",
      runId: "run",
      projectId: "proj",
      url: "https://example.com/products/miele",
      normalizedUrl: "https://example.com/products/miele",
      pageType: "product",
      source: "shopify_product",
      status: "analyzed",
      priority: "normal",
      title: "Miele",
      sourceEntityType: "shopify_product",
      sourceEntityId: "prod-1",
    };

    it("returns null for non product pages", () => {
      const item = buildGrowthAuditEconomicPriorityItem({
        page: {
          ...baseProductPage,
          pageType: "collection",
          sourceEntityType: "shopify_collection",
        },
        findings: [],
        tasks: [],
      });
      expect(item).toBeNull();
    });

    it("generates high priority for Shopify sales and high finding", () => {
      const findings: GrowthAuditFinding[] = [
        {
          id: "f1",
          runId: "run",
          projectId: "proj",
          pageId: "p1",
          category: "cro",
          title: "CTA debole",
          description: "CTA poco visibile",
          severity: "high",
          status: "open",
          createdAt: "2026-01-01T00:00:00Z",
        },
      ];
      const item = buildGrowthAuditEconomicPriorityItem({
        page: {
          ...baseProductPage,
          metadata: {
            shopifyCommerce: {
              sales: 450,
              quantitySold: 20,
              ordersCount: 15,
              syncedAt: "2026-01-01T00:00:00Z",
            },
            searchConsole: {
              impressions: 2000,
              ctr: 0.008,
              position: 10,
            },
          },
        },
        findings,
        tasks: [],
        peerContext: { salesValues: [100, 200, 450] },
      });
      expect(item).not.toBeNull();
      expect(item!.score).toBeGreaterThanOrEqual(60);
      expect(["high", "maximum"]).toContain(item!.level);
      expect(item!.reasons.some((r) => r.key === "shopify_sales")).toBe(true);
    });

    it("generates organic reason for high GSC impressions and low CTR", () => {
      const item = buildGrowthAuditEconomicPriorityItem({
        page: {
          ...baseProductPage,
          metadata: {
            searchConsole: {
              impressions: 3656,
              ctr: 0.0055,
              position: 8,
              topQueries: [{ query: "miele bio" }],
            },
          },
        },
        findings: [],
        tasks: [],
      });
      expect(item).not.toBeNull();
      expect(item!.breakdown.organicOpportunity).toBeGreaterThan(0);
      expect(
        item!.reasons.some((r) => r.key === "gsc_ctr") ||
          item!.shortReason.includes("impression"),
      ).toBe(true);
    });

    it("generates funnel reason for high itemViews and low purchases", () => {
      const item = buildGrowthAuditEconomicPriorityItem({
        page: {
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              itemViews: 10761,
              itemsAddedToCart: 1061,
              itemsPurchased: 0,
              itemRevenue: 50,
              matchedBy: "shopify_composite_item_id",
              matchDebug: {
                shopifyKeys: { productLegacyId: "1", variantLegacyIds: [], skus: [] },
                matchStatus: "matched",
                reason: "matched",
                candidateItems: [],
              },
              syncedAt: "2026-01-01T00:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
      });
      expect(item).not.toBeNull();
      expect(item!.breakdown.ecommerceFunnel).toBeGreaterThan(0);
      expect(
        item!.reasons.some((r) => r.key === "funnel_cart_purchase") ||
          item!.shortReason.includes("conversione"),
      ).toBe(true);
    });

    it("generates variant reason for bestVariantByRevenue", () => {
      const item = buildGrowthAuditEconomicPriorityItem({
        page: {
          ...baseProductPage,
          metadata: {
            shopifyCommerce: { sales: 200, syncedAt: "2026-01-01T00:00:00Z" },
            ga4Ecommerce: {
              itemViews: 500,
              itemsPurchased: 10,
              itemRevenue: 300,
              matchedBy: "shopify_composite_item_id",
              bestVariantByRevenue: "v500",
              variantBreakdown: [
                {
                  variantLegacyId: "v500",
                  variantTitle: "500g",
                  itemRevenue: 200,
                  itemsPurchased: 8,
                  matchedBy: "shopify_composite_item_id",
                },
                {
                  variantLegacyId: "v120",
                  variantTitle: "120g",
                  itemRevenue: 50,
                  itemsPurchased: 2,
                  matchedBy: "shopify_composite_item_id",
                },
              ],
              matchDebug: {
                shopifyKeys: { productLegacyId: "1", variantLegacyIds: ["v500"], skus: [] },
                matchStatus: "matched",
                reason: "matched",
                candidateItems: [],
              },
              syncedAt: "2026-01-01T00:00:00Z",
            },
          },
        },
        findings: [],
        tasks: [],
      });
      expect(item).not.toBeNull();
      expect(item!.metrics.bestVariantTitle).toBe("500g");
      expect(item!.reasons.some((r) => r.key === "best_variant")).toBe(true);
    });

    it("has low dataConfidence and prudent shortReason when data is missing", () => {
      const item = buildGrowthAuditEconomicPriorityItem({
        page: baseProductPage,
        findings: [],
        tasks: [],
      });
      expect(item).not.toBeNull();
      expect(item!.breakdown.dataConfidence).toBeLessThan(40);
      expect(item!.shortReason).toContain("Dati insufficienti");
      expect(item!.level).not.toBe("maximum");
    });

    it("ranking sorts by score descending", () => {
      const pages: GrowthAuditPage[] = [
        {
          ...baseProductPage,
          id: "low",
          title: "Low priority",
        },
        {
          ...baseProductPage,
          id: "high",
          title: "High priority",
          metadata: {
            shopifyCommerce: { sales: 800, syncedAt: "2026-01-01T00:00:00Z" },
            searchConsole: { impressions: 5000, ctr: 0.004, position: 7 },
            ga4Ecommerce: {
              itemViews: 2000,
              itemsAddedToCart: 200,
              itemsPurchased: 50,
              itemRevenue: 1200,
              matchedBy: "item_id",
              matchDebug: {
                shopifyKeys: { productLegacyId: "2", variantLegacyIds: [], skus: [] },
                matchStatus: "matched",
                reason: "matched",
                candidateItems: [],
              },
              syncedAt: "2026-01-01T00:00:00Z",
            },
          },
        },
      ];
      const ranking = buildGrowthAuditEconomicPriorityRanking({
        pages,
        findings: [],
        tasks: [],
        limit: 10,
      });
      expect(ranking.length).toBe(2);
      expect(ranking[0].pageId).toBe("high");
      expect(ranking[0].score).toBeGreaterThan(ranking[1].score);
    });

    it("filter with_sales shows only products with sales or revenue", () => {
      const items = [
        {
          pageId: "a",
          url: "https://a",
          title: "A",
          score: 80,
          level: "high" as const,
          label: "Priorità alta",
          shortReason: "test",
          reasons: [],
          breakdown: {
            businessImpact: 50,
            organicOpportunity: 0,
            trafficAndConversion: 0,
            ecommerceFunnel: 0,
            technicalAndCroRisk: 0,
            stockAndAvailability: 0,
            dataConfidence: 60,
          },
          metrics: { sales: 100 },
        },
        {
          pageId: "b",
          url: "https://b",
          title: "B",
          score: 30,
          level: "low" as const,
          label: "Priorità bassa",
          shortReason: "test",
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
      const filtered = filterGrowthAuditEconomicPriorityItems(items, "with_sales");
      expect(filtered).toHaveLength(1);
      expect(filtered[0].pageId).toBe("a");
    });

    it("filter incomplete_data shows only low confidence items", () => {
      const items = [
        {
          pageId: "a",
          url: "https://a",
          title: "A",
          score: 80,
          level: "high" as const,
          label: "Priorità alta",
          shortReason: "test",
          reasons: [],
          breakdown: {
            businessImpact: 50,
            organicOpportunity: 0,
            trafficAndConversion: 0,
            ecommerceFunnel: 0,
            technicalAndCroRisk: 0,
            stockAndAvailability: 0,
            dataConfidence: 60,
          },
          metrics: {},
        },
        {
          pageId: "b",
          url: "https://b",
          title: "B",
          score: 20,
          level: "monitor" as const,
          label: "Monitoraggio",
          shortReason: "test",
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
      const filtered = filterGrowthAuditEconomicPriorityItems(items, "incomplete_data");
      expect(filtered).toHaveLength(1);
      expect(filtered[0].pageId).toBe("b");
    });
  });
});
