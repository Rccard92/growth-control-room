export type IntegrationProvider =
  | "shopify"
  | "google_search_console"
  | "ga4"
  | "google_ads"
  | "google_pagespeed"
  | "google_crux"
  | "meta_ads"
  | "klaviyo"
  | "merchant_center"
  | "tiktok_ads";

export type IntegrationStatus = "not_connected" | "connected" | "error";

export type IntegrationUiStatus =
  | IntegrationStatus
  | "coming_soon"
  | "needs_setup"
  | "needs_reconnect"
  | "missing_credentials"
  | "setup_incomplete";

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
