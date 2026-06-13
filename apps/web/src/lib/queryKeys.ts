import type { DateRangeParams } from "@gcr/shared";

export const queryKeys = {
  projects: {
    all: ["projects"] as const,
    detail: (id: string) => ["projects", id] as const,
    integrations: (id: string) => ["projects", id, "integrations"] as const,
  },
  shopify: {
    status: (projectId: string) => ["shopify", projectId, "status"] as const,
    scopes: (projectId: string) => ["shopify", projectId, "scopes"] as const,
    dashboard: (projectId: string, dateRange?: DateRangeParams) =>
      [
        "shopify",
        projectId,
        "dashboard",
        dateRange?.range ?? null,
        dateRange?.startDate ?? null,
        dateRange?.endDate ?? null,
      ] as const,
    products: (projectId: string) => ["shopify", projectId, "products"] as const,
    orders: (projectId: string) => ["shopify", projectId, "orders"] as const,
  },
  contentSeo: {
    dashboard: (projectId: string) => ["contentSeo", projectId, "dashboard"] as const,
    products: (projectId: string) => ["contentSeo", projectId, "products"] as const,
    collections: (projectId: string) => ["contentSeo", projectId, "collections"] as const,
    proposals: (projectId: string) => ["contentSeo", projectId, "proposals"] as const,
    productAnalysis: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "productAnalysis", entityId] as const,
    collectionAnalysis: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "collectionAnalysis", entityId] as const,
    productDetail: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "productDetail", entityId] as const,
    collectionDetail: (projectId: string, entityId: string) =>
      ["contentSeo", projectId, "collectionDetail", entityId] as const,
    proposalDetail: (projectId: string, proposalId: string) =>
      ["contentSeo", projectId, "proposal", proposalId] as const,
    proposalPreview: (projectId: string, proposalId: string) =>
      ["contentSeo", projectId, "proposalPreview", proposalId] as const,
  },
  health: ["health"] as const,
};
