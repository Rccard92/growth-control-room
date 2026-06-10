export type IntegrationProvider =
  | "shopify"
  | "meta_ads"
  | "google_ads"
  | "klaviyo"
  | "ga4"
  | "google_search_console"
  | "merchant_center"
  | "tiktok_ads";

export type IntegrationStatus = "not_connected" | "connected" | "error";

export interface Integration {
  id: string | null;
  projectId: string;
  provider: IntegrationProvider;
  status: IntegrationStatus;
  connectedAt?: string;
}

export interface IntegrationMeta {
  provider: IntegrationProvider;
  label: string;
  description: string;
  icon: string;
}
