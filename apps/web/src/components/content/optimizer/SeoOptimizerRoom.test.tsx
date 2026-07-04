import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { SeoOptimizerRoom } from "./SeoOptimizerRoom";

const {
  useProductsSeoMock,
  useCollectionsSeoMock,
  useContentSeoDashboardMock,
  useProductSeoDetailMock,
  useCollectionSeoDetailMock,
  useShopifyScopesMock,
} = vi.hoisted(() => ({
  useProductsSeoMock: vi.fn(),
  useCollectionsSeoMock: vi.fn(),
  useContentSeoDashboardMock: vi.fn(),
  useProductSeoDetailMock: vi.fn(),
  useCollectionSeoDetailMock: vi.fn(),
  useShopifyScopesMock: vi.fn(),
}));

vi.mock("../../../hooks/useContentSeo", () => ({
  useProductsSeo: useProductsSeoMock,
  useCollectionsSeo: useCollectionsSeoMock,
  useContentSeoDashboard: useContentSeoDashboardMock,
  useProductSeoDetail: useProductSeoDetailMock,
  useCollectionSeoDetail: useCollectionSeoDetailMock,
}));

vi.mock("../../../hooks/useShopify", () => ({
  useShopifyScopes: useShopifyScopesMock,
}));

vi.mock("./SeoEntityEditDrawer", () => ({
  SeoEntityEditDrawer: () => null,
}));

function makeProductItem() {
  return {
    id: "p1",
    shopifyGid: "gid://shopify/Product/1",
    title: "Prodotto 1",
    score: 70,
    severity: "good" as const,
    mainIssues: [] as string[],
    quantitySold: 0,
    revenue: 0,
    hasProposal: false,
  };
}

function makeCollectionItem() {
  return {
    id: "c1",
    shopifyGid: "gid://shopify/Collection/1",
    title: "Categoria 1",
    score: 65,
    severity: "good" as const,
    mainIssues: [] as string[],
    productCount: 0,
    hasProposal: false,
  };
}

function setupMocks() {
  useProductsSeoMock.mockReturnValue({
    data: {
      items: [makeProductItem()],
      openaiConfigured: true,
      writeProductsAvailable: true,
    },
    isLoading: false,
  });
  useCollectionsSeoMock.mockReturnValue({
    data: {
      items: [makeCollectionItem()],
      openaiConfigured: true,
      writeProductsAvailable: true,
    },
    isLoading: false,
  });
  useContentSeoDashboardMock.mockReturnValue({
    data: { summary: { criticalIssues: 0, productsWithoutMeta: 0, collectionsWeak: 0 } },
    isLoading: false,
  });
  useProductSeoDetailMock.mockReturnValue({
    data: undefined,
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch: vi.fn(),
  });
  useCollectionSeoDetailMock.mockReturnValue({
    data: undefined,
    isLoading: false,
    isFetching: false,
    isError: false,
    refetch: vi.fn(),
  });
  useShopifyScopesMock.mockReturnValue({
    data: { canWriteProducts: true },
  });
}

describe("SeoOptimizerRoom", () => {
  it("shows Prodotti and Categorie tabs", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <SeoOptimizerRoom
        projectId="proj-1"
        connected
        feedback={null}
        onDismissFeedback={() => undefined}
      />,
    );

    expect(html).toContain("Prodotti");
    expect(html).toContain("Categorie");
  });

  it("does not show Audit SEO tab", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <SeoOptimizerRoom
        projectId="proj-1"
        connected
        feedback={null}
        onDismissFeedback={() => undefined}
      />,
    );

    expect(html).not.toContain("Audit SEO");
  });
});
