import { describe, expect, it } from "vitest";
import type { GoogleIntegrationStatusResponse } from "@gcr/shared";
import {
  buildProviderGraphLabel,
  getProviderGraphStatus,
} from "./IntegrationGraph";

const connectedGoogleStatus: GoogleIntegrationStatusResponse = {
  pagespeed: { status: "connected", configured: true },
  crux: { status: "connected", configured: true },
  oauth: { status: "connected", configured: true },
  searchConsole: { status: "connected", configured: true },
  analytics: { status: "connected", configured: true },
  googleAds: { status: "setup_incomplete", configured: true },
  merchantCenter: { status: "needs_setup", configured: true },
};

describe("IntegrationGraph status helpers", () => {
  it("maps Google providers from googleStatus when connected", () => {
    const statusMap = new Map([["shopify", "connected"]]);

    expect(getProviderGraphStatus("shopify", statusMap, connectedGoogleStatus)).toBe("connected");
    expect(getProviderGraphStatus("google_search_console", statusMap, connectedGoogleStatus)).toBe(
      "connected",
    );
    expect(getProviderGraphStatus("ga4", statusMap, connectedGoogleStatus)).toBe("connected");
    expect(getProviderGraphStatus("google_pagespeed", statusMap, connectedGoogleStatus)).toBe(
      "connected",
    );
    expect(getProviderGraphStatus("google_crux", statusMap, connectedGoogleStatus)).toBe("connected");
    expect(getProviderGraphStatus("google_ads", statusMap, connectedGoogleStatus)).toBe(
      "setup_incomplete",
    );
  });

  it("does not force non-Google providers to coming_soon when absent from API", () => {
    const statusMap = new Map([["shopify", "connected"]]);
    expect(getProviderGraphStatus("meta_ads", statusMap, connectedGoogleStatus)).toBe("coming_soon");
    expect(getProviderGraphStatus("klaviyo", statusMap, connectedGoogleStatus)).toBe("coming_soon");
  });

  it("builds labels with lock and warning suffixes", () => {
    expect(buildProviderGraphLabel("Meta Ads", "coming_soon")).toBe("Meta Ads 🔒");
    expect(buildProviderGraphLabel("Google Ads", "setup_incomplete")).toBe("Google Ads ⚠");
    expect(buildProviderGraphLabel("Google Search Console", "connected")).toBe(
      "Google Search Console",
    );
  });
});
