export interface ShopifyOAuthStartResponse {
  authorizationUrl: string;
}

export interface ShopifyConnectRequest {
  shopDomain: string;
  adminAccessToken: string;
}

export interface ShopifyConnectResponse {
  connected: boolean;
  shopDomain: string;
  shopName?: string | null;
  connectionStatus: string;
}

export interface ShopifyStatus {
  connected: boolean;
  shopDomain?: string | null;
  shopName?: string | null;
  lastSyncAt?: string | null;
}

export interface ShopifySyncResponse {
  productsSynced: number;
  ordersSynced: number;
  metricsSynced: number;
  lastSyncAt: string;
}

export interface ShopifyTopProduct {
  productGid: string;
  title: string;
  quantitySold: number;
}

export interface ShopifyProductSummary {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  status?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
}

export interface ShopifyOrderSummary {
  id: string;
  shopifyGid: string;
  orderName?: string | null;
  createdAtShopify?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  currency?: string | null;
  customerEmail?: string | null;
}

export interface ShopifyDashboardSummary {
  revenue: string;
  ordersCount: number;
  averageOrderValue: string;
  productsCount: number;
  activeProductsCount: number;
  draftProductsCount: number;
  outOfStockCount: number;
  lowStockCount: number;
  pendingOrdersCount: number;
  paidOrdersCount: number;
  lastSyncAt?: string | null;
  shopDomain: string;
}

export interface ShopifyDashboardProduct {
  title: string;
  status?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
  productType?: string | null;
  vendor?: string | null;
  handle?: string | null;
}

export interface ShopifyDashboardOrder {
  orderName?: string | null;
  createdAtShopify?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  currency?: string | null;
}

export interface ShopifyBestSeller {
  productTitle: string;
  quantitySold: number;
  revenue: string;
}

export interface ShopifySeoOpportunity {
  productTitle: string;
  issue: string;
  priority: string;
}

export type ShopifyInsightSeverity = "info" | "warning" | "critical" | "opportunity";

export interface ShopifyInsight {
  message: string;
  severity: ShopifyInsightSeverity;
}

export interface ShopifyDashboard {
  summary: ShopifyDashboardSummary;
  recentOrders: ShopifyDashboardOrder[];
  products: ShopifyDashboardProduct[];
  lowStockProducts: ShopifyDashboardProduct[];
  outOfStockProducts: ShopifyDashboardProduct[];
  bestSellers: ShopifyBestSeller[];
  staleProducts: ShopifyDashboardProduct[];
  seoOpportunities: ShopifySeoOpportunity[];
  insights: ShopifyInsight[];
}

export interface ShopifyProduct {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  status?: string | null;
  vendor?: string | null;
  productType?: string | null;
  totalInventory?: number | null;
  featuredImageUrl?: string | null;
  seoTitle?: string | null;
  seoDescription?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ShopifyOrder {
  id: string;
  shopifyGid: string;
  orderName?: string | null;
  createdAtShopify?: string | null;
  processedAt?: string | null;
  financialStatus?: string | null;
  fulfillmentStatus?: string | null;
  totalPrice: string;
  subtotalPrice?: string | null;
  currency?: string | null;
  customerEmail?: string | null;
  createdAt: string;
  updatedAt: string;
}
