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
  merchantCenter: { status: "needs_setup" as const, configured: true },
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

  it("maps connected GA4 without property to Seleziona proprietà", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "ga4")!;
    const onSelect = vi.fn();
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        analytics: { status: "connected", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      onSelectGoogleAnalyticsProperty: onSelect,
    });

    expect(props.actionLabel).toBe("Collegata");
    expect(props.disabled).toBe(true);
    expect(props.secondaryActionLabel).toBe("Seleziona proprietà");
    expect(props.onSecondaryAction).toBe(onSelect);
    expect(props.detailText).toBeUndefined();
  });

  it("maps connected GA4 with property to Modifica proprietà and detail", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "ga4")!;
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        analytics: { status: "connected", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      googleAnalyticsPropertyId: "123456789",
      googleAnalyticsPropertyName: "Solmielato GA4",
      onSelectGoogleAnalyticsProperty: vi.fn(),
    });

    expect(props.secondaryActionLabel).toBe("Modifica proprietà");
    expect(props.detailText).toBe("Proprietà: Solmielato GA4");
  });

  it("maps merchant_center without account to Seleziona account", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "merchant_center")!;
    const onSelect = vi.fn();
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        oauth: { status: "connected", configured: true },
        merchantCenter: { status: "needs_setup", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      onSelectMerchantAccount: onSelect,
    });

    expect(props.badgeLabel).toBe("Account da selezionare");
    expect(props.secondaryActionLabel).toBe("Seleziona account");
    expect(props.onSecondaryAction).toBe(onSelect);
  });

  it("maps merchant_center needs_reconnect to Aggiungi permessi Merchant", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "merchant_center")!;
    const reconnect = vi.fn();
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        oauth: { status: "connected", configured: true },
        merchantCenter: {
          status: "needs_reconnect",
          configured: true,
          message: "Ricollega Google per concedere i permessi Merchant Center.",
        },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      handleReconnectGoogle: reconnect,
      projectId: "proj-1",
    });

    expect(props.badgeLabel).toBe("Da ricollegare");
    expect(props.actionLabel).toBe("Aggiungi permessi Merchant");
    props.onAction?.();
    expect(reconnect).toHaveBeenCalledWith("merchant_center", "add_scope");
  });

  it("maps merchant_center with account to Configurata", () => {
    const meta = INTEGRATIONS.find((item) => item.provider === "merchant_center")!;
    const props = getIntegrationCardProps({
      meta,
      googleStatus: {
        ...googleStatus,
        oauth: { status: "connected", configured: true },
        merchantCenter: { status: "connected", configured: true },
      },
      oauthConnectDisabled: false,
      handleConnectGoogle: vi.fn(),
      projectId: "proj-1",
      googleMerchantAccountId: "123456",
      googleMerchantAccountName: "Example Merchant",
      onSelectMerchantAccount: vi.fn(),
    });

    expect(props.badgeLabel).toBe("Configurata");
    expect(props.detailText).toBe("Account: Example Merchant");
  });
});
