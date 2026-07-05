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

  it("maps connected Search Console without property to Seleziona proprietà", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "google_search_console")!;
    const onSelect = vi.fn();
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      onSelectSearchConsoleProperty: onSelect,
    });

    expect(props.actionLabel).toBe("Collegata");
    expect(props.disabled).toBe(true);
    expect(props.secondaryActionLabel).toBe("Seleziona proprietà");
    expect(props.onSecondaryAction).toBe(onSelect);
    expect(props.detailText).toBeUndefined();
  });

  it("maps connected Search Console with property to Modifica proprietà and detail", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "google_search_console")!;
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      searchConsoleSiteUrl: "https://solmielato.it/",
      onSelectSearchConsoleProperty: vi.fn(),
    });

    expect(props.secondaryActionLabel).toBe("Modifica proprietà");
    expect(props.detailText).toBe("Proprietà: https://solmielato.it/");
  });
});
