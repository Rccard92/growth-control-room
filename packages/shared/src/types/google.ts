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
}

export interface GoogleOAuthStartRequest {
  services?: string[];
}

export interface GoogleOAuthStartResponse {
  authorizationUrl: string;
}
