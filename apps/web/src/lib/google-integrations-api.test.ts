import { describe, expect, it, vi } from "vitest";
import {
  fetchGoogleIntegrationStatus,
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
});
