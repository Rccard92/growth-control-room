import type {
  DateRangeParams,
  ShopifyConnectRequest,
  ShopifyConnectResponse,
  ShopifyDashboard,
  ShopifyOAuthStartResponse,
  ShopifyOrder,
  ShopifyProduct,
  ShopifyStatus,
  ShopifyScopesResponse,
  ShopifySyncResponse,
} from "@gcr/shared";
import { dateRangeToApiQueryString } from "./date-range";
import { apiFetch } from "./api";

export function startShopifyOAuth(
  projectId: string,
  shopDomain: string,
): Promise<ShopifyOAuthStartResponse> {
  const params = new URLSearchParams({ shop: shopDomain.trim() });
  return apiFetch<ShopifyOAuthStartResponse>(
    `/api/projects/${projectId}/integrations/shopify/oauth/start?${params.toString()}`,
  );
}

export function connectShopify(
  projectId: string,
  body: ShopifyConnectRequest,
): Promise<ShopifyConnectResponse> {
  return apiFetch<ShopifyConnectResponse>(
    `/api/projects/${projectId}/integrations/shopify/connect`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shop_domain: body.shopDomain,
        admin_access_token: body.adminAccessToken,
      }),
    },
  );
}

export function getShopifyStatus(projectId: string): Promise<ShopifyStatus> {
  return apiFetch<ShopifyStatus>(`/api/projects/${projectId}/shopify/status`);
}

export function getShopifyScopes(projectId: string): Promise<ShopifyScopesResponse> {
  return apiFetch<ShopifyScopesResponse>(`/api/projects/${projectId}/shopify/scopes`);
}

export function syncShopify(projectId: string): Promise<ShopifySyncResponse> {
  return apiFetch<ShopifySyncResponse>(`/api/projects/${projectId}/shopify/sync`, {
    method: "POST",
  });
}

export function getShopifyDashboard(
  projectId: string,
  dateRange?: DateRangeParams,
): Promise<ShopifyDashboard> {
  const query = dateRange ? `?${dateRangeToApiQueryString(dateRange)}` : "";
  return apiFetch<ShopifyDashboard>(`/api/projects/${projectId}/shopify/dashboard${query}`);
}

export function getShopifyProducts(projectId: string): Promise<ShopifyProduct[]> {
  return apiFetch<ShopifyProduct[]>(`/api/projects/${projectId}/shopify/products`);
}

export function getShopifyOrders(projectId: string): Promise<ShopifyOrder[]> {
  return apiFetch<ShopifyOrder[]>(`/api/projects/${projectId}/shopify/orders`);
}
