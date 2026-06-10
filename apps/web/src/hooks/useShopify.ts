import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  connectShopify,
  startShopifyOAuth,
  getShopifyDashboard,
  getShopifyOrders,
  getShopifyProducts,
  getShopifyStatus,
  syncShopify,
} from "../lib/shopify-api";
import { queryKeys } from "../lib/queryKeys";
import type { DateRangeParams, ShopifyConnectRequest } from "@gcr/shared";

export function useShopifyStatus(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.shopify.status(projectId ?? ""),
    queryFn: () => getShopifyStatus(projectId!),
    enabled: Boolean(projectId),
  });
}

export function useShopifyDashboard(
  projectId: string | undefined,
  connected: boolean,
  dateRange?: DateRangeParams,
) {
  return useQuery({
    queryKey: queryKeys.shopify.dashboard(projectId ?? "", dateRange),
    queryFn: () => getShopifyDashboard(projectId!, dateRange),
    enabled: Boolean(projectId) && connected,
  });
}

export function useShopifyProducts(projectId: string | undefined, connected: boolean) {
  return useQuery({
    queryKey: queryKeys.shopify.products(projectId ?? ""),
    queryFn: () => getShopifyProducts(projectId!),
    enabled: Boolean(projectId) && connected,
  });
}

export function useShopifyOrders(projectId: string | undefined, connected: boolean) {
  return useQuery({
    queryKey: queryKeys.shopify.orders(projectId ?? ""),
    queryFn: () => getShopifyOrders(projectId!),
    enabled: Boolean(projectId) && connected,
  });
}

export function useShopifyOAuthStart(projectId: string) {
  return useMutation({
    mutationFn: async (shopDomain: string) => {
      const result = await startShopifyOAuth(projectId, shopDomain);
      window.location.href = result.authorizationUrl;
    },
  });
}

export function useShopifyConnect(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ShopifyConnectRequest) => connectShopify(projectId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.shopify.status(projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.integrations(projectId),
      });
    },
  });
}

export function useShopifySync(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => syncShopify(projectId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.shopify.status(projectId) });
      void queryClient.invalidateQueries({
        queryKey: ["shopify", projectId, "dashboard"],
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.shopify.products(projectId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.shopify.orders(projectId) });
    },
  });
}
