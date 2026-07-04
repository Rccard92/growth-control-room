import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { SeoProductDetailResponse } from "@gcr/shared";
import { SeoEntityEditPanel } from "./SeoEntityEditPanel";

const {
  useApplyEntityFieldsMock,
  useSaveManualProposalMock,
  useSyncCollectionSeoMock,
  useSyncMetafieldDefinitionsMock,
  useSyncProductSeoMock,
  useSeoAiQueueMock,
} = vi.hoisted(() => ({
  useApplyEntityFieldsMock: vi.fn(),
  useSaveManualProposalMock: vi.fn(),
  useSyncCollectionSeoMock: vi.fn(),
  useSyncMetafieldDefinitionsMock: vi.fn(),
  useSyncProductSeoMock: vi.fn(),
  useSeoAiQueueMock: vi.fn(),
}));

vi.mock("../../../hooks/useContentSeo", () => ({
  useApplyEntityFields: useApplyEntityFieldsMock,
  useSaveManualProposal: useSaveManualProposalMock,
  useSyncCollectionSeo: useSyncCollectionSeoMock,
  useSyncMetafieldDefinitions: useSyncMetafieldDefinitionsMock,
  useSyncProductSeo: useSyncProductSeoMock,
}));

vi.mock("../../../hooks/useSeoAiQueue", () => ({
  useSeoAiQueue: useSeoAiQueueMock,
}));

function makeProductDetail(): SeoProductDetailResponse {
  return {
    product: { title: "Miele" },
    currentValues: {
      title: "Miele",
      metaDescription: "Descrizione",
      handle: "miele",
    },
    images: [],
    quantitySold: 0,
    revenue: 0,
    proposalHistory: [],
    changeLogs: [],
    openaiConfigured: true,
    writeProductsAvailable: true,
  } as SeoProductDetailResponse;
}

function setupMutationMocks() {
  const idleMutation = {
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
  };
  useApplyEntityFieldsMock.mockReturnValue(idleMutation);
  useSaveManualProposalMock.mockReturnValue(idleMutation);
  useSyncCollectionSeoMock.mockReturnValue(idleMutation);
  useSyncMetafieldDefinitionsMock.mockReturnValue(idleMutation);
  useSyncProductSeoMock.mockReturnValue(idleMutation);
  useSeoAiQueueMock.mockReturnValue({
    enqueue: vi.fn(),
    isRunning: false,
    cancel: vi.fn(),
  });
}

describe("SeoEntityEditPanel", () => {
  it("renders skeleton when detailLoading in embedded mode", () => {
    setupMutationMocks();
    const html = renderToStaticMarkup(
      <SeoEntityEditPanel
        embedded
        projectId="proj-1"
        entityType="product"
        entityId="prod-1"
        title="Miele"
        detailLoading
        openaiConfigured
        writeProductsAvailable
      />,
    );

    expect(html).toContain("seo-edit-drawer__skeleton");
    expect(html).toContain('aria-busy="true"');
    expect(html).toContain("seo-entity-edit-panel--embedded");
  });

  it("renders editor tabs when product detail is available", () => {
    setupMutationMocks();
    const html = renderToStaticMarkup(
      <SeoEntityEditPanel
        embedded
        projectId="proj-1"
        entityType="product"
        entityId="prod-1"
        title="Miele"
        productDetail={makeProductDetail()}
        openaiConfigured
        writeProductsAvailable
      />,
    );

    expect(html).toContain("Principale");
    expect(html).toContain("seo-entity-edit-panel__embedded-toolbar");
  });
});
