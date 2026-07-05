export type GoogleServiceStatusValue =
  | "not_connected"
  | "connected"
  | "needs_setup"
  | "missing_credentials"
  | "setup_incomplete";

export interface GoogleServiceStatus {
  status: GoogleServiceStatusValue;
  configured?: boolean | null;
  message?: string | null;
}

export interface GoogleIntegrationStatusResponse {
  pagespeed: GoogleServiceStatus;
  crux: GoogleServiceStatus;
  oauth: GoogleServiceStatus;
  searchConsole: GoogleServiceStatus;
  analytics: GoogleServiceStatus;
  googleAds: GoogleServiceStatus;
  merchantCenter: GoogleServiceStatus;
}

export interface GoogleOAuthStartRequest {
  services?: string[];
}

export interface GoogleOAuthStartResponse {
  authorizationUrl: string;
}

export interface GoogleSearchConsoleSite {
  siteUrl: string;
  permissionLevel?: string | null;
}

export interface GoogleSearchConsoleSitesResponse {
  sites: GoogleSearchConsoleSite[];
}

export interface SelectSearchConsoleSiteRequest {
  siteUrl: string;
}

export interface SelectSearchConsoleSiteResponse {
  siteUrl: string;
  message: string;
}

export interface GoogleAnalyticsProperty {
  propertyId: string;
  propertyName: string;
  displayName: string;
  accountDisplayName?: string | null;
}

export interface GoogleAnalyticsPropertiesResponse {
  properties: GoogleAnalyticsProperty[];
}

export interface SelectGoogleAnalyticsPropertyRequest {
  propertyId: string;
  propertyName: string;
  displayName: string;
}

export interface SelectGoogleAnalyticsPropertyResponse {
  propertyId: string;
  propertyName: string;
  displayName: string;
  message: string;
}

export interface GoogleMerchantAccount {
  accountId: string;
  name: string;
  displayName: string;
  type?: string | null;
  relationship?: string | null;
}

export interface GoogleMerchantAccountsResponse {
  accounts: GoogleMerchantAccount[];
}

export interface SelectGoogleMerchantAccountRequest {
  accountId: string;
  accountName: string;
}

export interface SelectGoogleMerchantAccountResponse {
  accountId: string;
  message: string;
}
