export type IntegrationType =
  | "shopify"
  | "meta_ads"
  | "google_ads"
  | "klaviyo"
  | "gsc"
  | "ga4"
  | "merchant_center"
  | "tiktok";

export type IntegrationStatus = "disconnected" | "connected" | "error";

export interface Integration {
  id: string;
  projectId: string;
  type: IntegrationType;
  status: IntegrationStatus;
  connectedAt?: string;
}

export interface IntegrationMeta {
  type: IntegrationType;
  label: string;
  description: string;
  icon: string;
}
