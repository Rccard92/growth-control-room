import { describe, expect, it, vi } from "vitest";
import { INTEGRATIONS } from "@gcr/shared";
import { getIntegrationCardProps } from "./integration-card-props";

const googleStatus = {
  pagespeed: { status: "connected" as const, configured: true },
  crux: { status: "connected" as const, configured: true },
  oauth: { status: "connected" as const, configured: true },
  searchConsole: { status: "needs_setup" as const, configured: true },
  analytics: { status: "needs_setup" as const, configured: true },
  googleAds: { status: "setup_incomplete" as const, configured: true },
};

describe("getIntegrationCardProps", () => {
  it("maps Shopify connected to Gestisci", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "shopify")!;
    const props = getIntegrationCardProps({
      meta,
      apiStatus: "connected",
      googleStatus,
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
    });

    expect(props.actionLabel).toBe("Gestisci");
    expect(props.href).toBe("/projects/proj-1/shopify");
  });

  it("maps PageSpeed configured to Configurata", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "google_pagespeed")!;
    const props = getIntegrationCardProps({
      meta,
      googleStatus,
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
    });

    expect(props.badgeLabel).toBe("Configurata");
    expect(props.actionLabel).toBe("Configurata");
    expect(props.disabled).toBe(true);
  });

  it("maps Google Ads setup_incomplete to developer token note", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "google_ads")!;
    const props = getIntegrationCardProps({
      meta,
      googleStatus,
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
    });

    expect(props.actionLabel).toBe("Developer Token mancante");
    expect(props.note).toContain("GOOGLE_ADS_DEVELOPER_TOKEN");
    expect(props.disabled).toBe(true);
  });
});
