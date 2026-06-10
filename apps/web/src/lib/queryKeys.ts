export const queryKeys = {
  projects: {
    all: ["projects"] as const,
    detail: (id: string) => ["projects", id] as const,
    integrations: (id: string) => ["projects", id, "integrations"] as const,
  },
  shopify: {
    status: (projectId: string) => ["shopify", projectId, "status"] as const,
    dashboard: (projectId: string) => ["shopify", projectId, "dashboard"] as const,
    products: (projectId: string) => ["shopify", projectId, "products"] as const,
    orders: (projectId: string) => ["shopify", projectId, "orders"] as const,
  },
  health: ["health"] as const,
};
