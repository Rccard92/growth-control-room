import type { IntegrationMeta, IntegrationType } from "../types/integration";

export const INTEGRATIONS: IntegrationMeta[] = [
  {
    type: "shopify",
    label: "Shopify",
    description: "Store e-commerce, ordini, prodotti e inventario",
    icon: "🛍️",
  },
  {
    type: "meta_ads",
    label: "Meta Ads",
    description: "Campagne Facebook e Instagram Ads",
    icon: "📱",
  },
  {
    type: "google_ads",
    label: "Google Ads",
    description: "Campagne search, display e shopping",
    icon: "🔍",
  },
  {
    type: "klaviyo",
    label: "Klaviyo",
    description: "Email marketing e automazioni",
    icon: "✉️",
  },
  {
    type: "gsc",
    label: "Google Search Console",
    description: "Prestazioni SEO e indicizzazione",
    icon: "📊",
  },
  {
    type: "ga4",
    label: "Google Analytics 4",
    description: "Traffico web e conversioni",
    icon: "📈",
  },
  {
    type: "merchant_center",
    label: "Merchant Center",
    description: "Feed prodotti Google Shopping",
    icon: "🏪",
  },
  {
    type: "tiktok",
    label: "TikTok Ads",
    description: "Campagne pubblicitarie TikTok",
    icon: "🎵",
  },
];

export const INTEGRATION_BY_TYPE: Record<IntegrationType, IntegrationMeta> =
  Object.fromEntries(INTEGRATIONS.map((i) => [i.type, i])) as Record<
    IntegrationType,
    IntegrationMeta
  >;
