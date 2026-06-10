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

export interface ShopifyDashboard {
  revenue: string;
  ordersCount: number;
  averageOrderValue: string;
  productsCount: number;
  lowStockProducts: ShopifyProductSummary[];
  topProducts: ShopifyTopProduct[];
  recentOrders: ShopifyOrderSummary[];
  lastSyncAt?: string | null;
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
