import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditPage } from "@gcr/shared";
import { GrowthAuditPageWorkspaceGa4EcommerceSection } from "./GrowthAuditPageWorkspaceGa4EcommerceSection";

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

describe("GrowthAuditPageWorkspaceGa4EcommerceSection", () => {
  it("renders nothing for non product pages", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
          ...baseProductPage,
          pageType: "collection",
          sourceEntityType: "shopify_collection",
        }}
      />,
    );
    expect(html).toBe("");
  });

  it("renders empty state when funnel metadata is missing", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection page={baseProductPage} />,
    );
    expect(html).toContain('id="ga4-ecommerce-funnel"');
    expect(html).toContain("GA4 Ecommerce Funnel");
    expect(html).toContain("non ha ancora dati funnel ecommerce GA4");
  });

  it("renders funnel steps and diagnosis for high views zero cart", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
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
              cartToCheckoutRate: 0,
              checkoutToPurchaseRate: 0,
              viewToPurchaseRate: 0,
              cartToPurchaseRate: 0,
              matchedBy: "item_id",
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("View item");
    expect(html).toContain("Add to cart");
    expect(html).toContain("Begin checkout");
    expect(html).toContain("Purchase");
    expect(html).toContain("non entra nel carrello");
  });

  it("renders diagnosis for cart without purchase", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 80,
              itemsAddedToCart: 10,
              itemsCheckedOut: 0,
              itemsPurchased: 0,
              itemRevenue: 0,
              matchedBy: "item_id",
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("non iniziano il checkout");
  });
});
