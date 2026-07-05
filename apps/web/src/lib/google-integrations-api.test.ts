import { describe, expect, it, vi } from "vitest";
import {
  fetchGoogleAnalyticsProperties,
  fetchGoogleIntegrationStatus,
  fetchSearchConsoleSites,
  selectGoogleAnalyticsProperty,
  selectSearchConsoleSite,
  startGoogleOAuth,
} from "./google-integrations-api";

vi.mock("./api", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "./api";

describe("google-integrations-api", () => {
  it("builds google status path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      pagespeed: { status: "connected", configured: true },
      crux: { status: "connected", configured: true },
      oauth: { status: "connected", configured: true },
      searchConsole: { status: "needs_setup", configured: true },
      analytics: { status: "needs_setup", configured: true },
      googleAds: { status: "setup_incomplete", configured: true },
    });

    await fetchGoogleIntegrationStatus("proj-1");

    expect(apiFetch).toHaveBeenCalledWith("/api/projects/proj-1/google/status");
  });

  it("builds google oauth start path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      authorizationUrl: "https://accounts.google.com/o/oauth2/v2/auth?client_id=test",
    });

    await startGoogleOAuth("proj-1", {
      services: ["search_console", "analytics", "google_ads"],
    });

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/google/oauth/start",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          services: ["search_console", "analytics", "google_ads"],
        }),
      }),
    );
  });

  it("builds search console sites path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      sites: [{ siteUrl: "https://example.com/", permissionLevel: "siteOwner" }],
    });

    await fetchSearchConsoleSites("proj-1");

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/google/search-console/sites",
    );
  });

  it("builds select search console site path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      siteUrl: "https://example.com/",
      message: "Proprietà Search Console salvata.",
    });

    await selectSearchConsoleSite("proj-1", { siteUrl: "https://example.com/" });

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/google/search-console/select-site",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ siteUrl: "https://example.com/" }),
      }),
    );
  });

  it("builds google analytics properties path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      properties: [
        {
          propertyId: "123456789",
          propertyName: "properties/123456789",
          displayName: "Example GA4",
        },
      ],
    });

    await fetchGoogleAnalyticsProperties("proj-1");

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/google/analytics/properties",
    );
  });

  it("builds select google analytics property path", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      propertyId: "123456789",
      propertyName: "properties/123456789",
      displayName: "Example GA4",
      message: "Proprietà GA4 salvata.",
    });

    await selectGoogleAnalyticsProperty("proj-1", {
      propertyId: "123456789",
      propertyName: "properties/123456789",
      displayName: "Example GA4",
    });

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/projects/proj-1/google/analytics/select-property",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          propertyId: "123456789",
          propertyName: "properties/123456789",
          displayName: "Example GA4",
        }),
      }),
    );
  });
});
