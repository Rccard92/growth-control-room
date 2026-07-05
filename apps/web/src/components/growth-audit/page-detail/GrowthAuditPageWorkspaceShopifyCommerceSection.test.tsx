import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageWorkspaceShopifyCommerceSection } from "./GrowthAuditPageWorkspaceShopifyCommerceSection";

const baseProductPage: GrowthAuditPage = {
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
  sourceEntityType: "shopify_product",
  sourceEntityId: "prod-1",
};

describe("GrowthAuditPageWorkspaceShopifyCommerceSection", () => {
  it("renders nothing for non product pages", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceShopifyCommerceSection
        page={{
          ...baseProductPage,
          pageType: "collection",
          sourceEntityType: "shopify_collection",
        }}
      />,
    );
    expect(html).toBe("");
  });

  it("renders empty state when commerce metadata is missing", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceShopifyCommerceSection page={baseProductPage} />,
    );
    expect(html).toContain('id="shopify-commerce"');
    expect(html).toContain("Shopify Commerce");
    expect(html).toContain("non ha ancora dati ecommerce Shopify");
  });

  it("renders commerce metrics when metadata is present", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceShopifyCommerceSection
        page={{
          ...baseProductPage,
          metadata: {
            shopifyCommerce: {
              periodDays: 30,
              sales: 345.6,
              quantitySold: 12,
              ordersCount: 8,
              currency: "EUR",
              stock: 42,
              availableForSale: true,
              priceMin: 12.9,
              priceMax: 24.9,
              productStatus: "ACTIVE",
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("Revenue / Sales");
    expect(html).toContain("345,60 EUR");
    expect(html).toContain("Quantità venduta");
    expect(html).toContain("Ordini");
    expect(html).toContain("Stock");
    expect(html).toContain("Disponibile");
    expect(html).toContain("ACTIVE");
  });
});
