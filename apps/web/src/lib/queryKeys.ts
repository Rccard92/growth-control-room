import type { DateRangeParams } from "@gcr/shared";

export const queryKeys = {
  projects: {
    all: ["projects"] as const,
    detail: (id: string) => ["projects", id] as const,
    integrations: (id: string) => ["projects", id, "integrations"] as const,
  },
  shopify: {
    status: (projectId: string) => ["shopify", projectId, "status"] as const,
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
  },
  health: ["health"] as const,
};
