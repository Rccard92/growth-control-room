import type { IntegrationProvider } from "@gcr/shared";

import shopifyLogo from "../assets/integrations/shopify.svg";
import metaAdsLogo from "../assets/integrations/meta-ads.svg";
import googleAdsLogo from "../assets/integrations/google-ads.svg";
import googleAnalyticsLogo from "../assets/integrations/google-analytics-4.svg";
import googleSearchConsoleLogo from "../assets/integrations/google-search-console.svg";
import googleMerchantCenterLogo from "../assets/integrations/google-merchant-center.svg";
import googlePageSpeedLogo from "../assets/integrations/google-pagespeed-insights.svg";
import chromeUxReportLogo from "../assets/integrations/chrome-ux-report.svg";
import tiktokAdsLogo from "../assets/integrations/tiktok-ads.svg";
import klaviyoLogo from "../assets/integrations/klaviyo.svg";

export const INTEGRATION_BRAND_ICONS: Partial<Record<IntegrationProvider, string>> = {
  shopify: shopifyLogo,
  meta_ads: metaAdsLogo,
  google_ads: googleAdsLogo,
  ga4: googleAnalyticsLogo,
  google_search_console: googleSearchConsoleLogo,
  merchant_center: googleMerchantCenterLogo,
  google_pagespeed: googlePageSpeedLogo,
  google_crux: chromeUxReportLogo,
  tiktok_ads: tiktokAdsLogo,
  klaviyo: klaviyoLogo,
};
