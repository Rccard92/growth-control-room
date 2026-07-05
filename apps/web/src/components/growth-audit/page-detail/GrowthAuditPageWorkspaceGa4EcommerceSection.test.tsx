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
              matchDebug: {
                shopifyKeys: {
                  productGid: "gid://shopify/Product/1",
                  productLegacyId: "1",
                  variantLegacyIds: [],
                  skus: [],
                  titleNormalized: "miele",
                  handleNormalized: "miele",
                },
                matchedBy: "item_id",
                matchStatus: "matched",
                reason: "Prodotto abbinato tramite item_id.",
                candidateItems: [],
              },
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
    expect(html).toContain("Match affidabile tramite");
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

  it("renders no-match debug block with shopify keys and candidates", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
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
                  productGid: "gid://shopify/Product/123",
                  productLegacyId: "123",
                  variantLegacyIds: ["456"],
                  skus: ["sku-miele"],
                  titleNormalized: "miele premium",
                  handleNormalized: "miele",
                },
                matchedBy: "none",
                matchStatus: "no_reliable_match",
                reason:
                  "Nessuna riga GA4 ha itemId/SKU/title uguale alle chiavi Shopify del prodotto.",
                candidateItems: [
                  {
                    itemId: "999",
                    itemName: "Miele Premium Bio",
                    itemVariant: "",
                    itemsViewed: 80,
                    itemsAddedToCart: 4,
                    itemsPurchased: 1,
                    itemRevenue: 12.9,
                    candidateReason:
                      "Nome simile ma non identico: non assegnato automaticamente.",
                  },
                ],
              },
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("Dati GA4 non abbinati a questo prodotto");
    expect(html).toContain("evitare dati falsati");
    expect(html).toContain("Product legacy id");
    expect(html).toContain("123");
    expect(html).toContain("sku-miele");
    expect(html).toContain("Possibili item GA4 da verificare manualmente");
    expect(html).toContain("Questi dati non sono stati assegnati al prodotto");
    expect(html).not.toContain("View item");
  });

  it("renders zero-data message when metadata is synced but empty without match debug", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 0,
              itemsAddedToCart: 0,
              itemsCheckedOut: 0,
              itemsPurchased: 0,
              itemRevenue: 0,
              matchedBy: "none",
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("View item");
    expect(html).toContain("Nessun dato ecommerce item-level trovato per questo periodo");
    expect(html).toContain("Prova 90 giorni");
  });

  it("renders composite match label, funnel and GA4 itemId without no-match block", () => {
    const compositeItemId = "shopify_IT_14916300964188_54906504773980";
    const html = renderToStaticMarkup(
      <GrowthAuditPageWorkspaceGa4EcommerceSection
        page={{
          ...baseProductPage,
          metadata: {
            ga4Ecommerce: {
              periodDays: 30,
              itemViews: 10089,
              itemsAddedToCart: 1061,
              itemsCheckedOut: 400,
              itemsPurchased: 307,
              itemRevenue: 2425.3,
              viewToCartRate: 0.1052,
              cartToPurchaseRate: 0.2893,
              matchedBy: "shopify_composite_item_id",
              matchedItemIds: [compositeItemId],
              matchDebug: {
                shopifyKeys: {
                  productGid: "gid://shopify/Product/14916300964188",
                  productLegacyId: "14916300964188",
                  variantLegacyIds: ["54906504773980"],
                  skus: [],
                  titleNormalized: "miele",
                  handleNormalized: "miele",
                },
                matchedBy: "shopify_composite_item_id",
                matchStatus: "matched",
                reason:
                  "Prodotto abbinato tramite itemId Shopify composto: product legacy id e/o variant id coincidono.",
                candidateItems: [],
              },
              syncedAt: "2026-06-13T10:00:00.000Z",
            },
          },
        }}
      />,
    );
    expect(html).toContain("Shopify composite itemId");
    expect(html).toContain("itemId GA4");
    expect(html).toContain(compositeItemId);
    expect(html).toContain("View item");
    expect(html).toContain("Purchase");
    expect(html).not.toContain("Dati GA4 non abbinati a questo prodotto");
  });
});
