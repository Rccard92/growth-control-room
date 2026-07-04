import { describe, expect, it } from "vitest";
import type { GrowthAuditPage } from "@gcr/shared";
import {
  aggregatePageInventory,
  filterInventoryPages,
  getDefaultRootUrl,
  getGrowthAuditInventoryFilterLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditStatusLabel,
  getInventoryMessage,
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
  });

  it("builds default root URL from shop domain", () => {
    expect(getDefaultRootUrl("shop.example.com")).toBe("https://shop.example.com");
    expect(getDefaultRootUrl("https://shop.example.com")).toBe("https://shop.example.com");
  });
});
