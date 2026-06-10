import type {
  ShopifyConnectRequest,
  ShopifyConnectResponse,
  ShopifyDashboard,
  ShopifyOrder,
  ShopifyProduct,
  ShopifyStatus,
  ShopifySyncResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

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

export function syncShopify(projectId: string): Promise<ShopifySyncResponse> {
  return apiFetch<ShopifySyncResponse>(`/api/projects/${projectId}/shopify/sync`, {
    method: "POST",
  });
}

export function getShopifyDashboard(projectId: string): Promise<ShopifyDashboard> {
  return apiFetch<ShopifyDashboard>(`/api/projects/${projectId}/shopify/dashboard`);
}

export function getShopifyProducts(projectId: string): Promise<ShopifyProduct[]> {
  return apiFetch<ShopifyProduct[]>(`/api/projects/${projectId}/shopify/products`);
}

export function getShopifyOrders(projectId: string): Promise<ShopifyOrder[]> {
  return apiFetch<ShopifyOrder[]>(`/api/projects/${projectId}/shopify/orders`);
}
