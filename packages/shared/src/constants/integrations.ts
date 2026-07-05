import type { IntegrationMeta, IntegrationProvider } from "../types/integration";

export const INTEGRATIONS: IntegrationMeta[] = [
  {
    provider: "shopify",
    label: "Shopify",
    description: "Store e-commerce, ordini, prodotti e inventario",
    icon: "🛍️",
  },
  {
    provider: "google_search_console",
    label: "Google Search Console",
    description: "Prestazioni SEO e indicizzazione",
    icon: "🔎",
  },
  {
    provider: "ga4",
    label: "Google Analytics 4",
    description: "Traffico web e conversioni",
    icon: "📈",
  },
  {
    provider: "google_ads",
    label: "Google Ads",
    description: "Campagne search, display e shopping",
    icon: "🎯",
  },
  {
    provider: "google_pagespeed",
    label: "PageSpeed Insights",
    description: "Performance, Lighthouse e controlli lab per le pagine prioritarie",
    icon: "⚡",
  },
  {
    provider: "google_crux",
    label: "Chrome UX Report",
    description: "Core Web Vitals real-user per esperienza reale",
    icon: "📊",
  },
  {
    provider: "meta_ads",
    label: "Meta Ads",
    description: "Campagne Facebook e Instagram Ads",
    icon: "📱",
  },
  {
    provider: "klaviyo",
    label: "Klaviyo",
    description: "Email marketing e automazioni",
    icon: "✉️",
  },
  {
    provider: "merchant_center",
    label: "Merchant Center",
    description: "Feed prodotti Google Shopping",
    icon: "🏪",
  },
  {
    provider: "tiktok_ads",
    label: "TikTok Ads",
    description: "Campagne pubblicitarie TikTok",
    icon: "🎵",
  },
];

export const INTEGRATION_BY_PROVIDER: Record<
  IntegrationProvider,
  IntegrationMeta
> = Object.fromEntries(INTEGRATIONS.map((i) => [i.provider, i])) as Record<
  IntegrationProvider,
  IntegrationMeta
>;
