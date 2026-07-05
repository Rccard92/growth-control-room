import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { IntegrationsPage } from "./IntegrationsPage";

const {
  useParamsMock,
  useProjectMock,
  useProjectIntegrationsMock,
  useGoogleIntegrationStatusMock,
  useStartGoogleOAuthMock,
  useSearchConsoleSitesMock,
  useSelectSearchConsoleSiteMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useProjectIntegrationsMock: vi.fn(),
  useGoogleIntegrationStatusMock: vi.fn(),
  useStartGoogleOAuthMock: vi.fn(),
  useSearchConsoleSitesMock: vi.fn(),
  useSelectSearchConsoleSiteMock: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: useParamsMock,
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

vi.mock("react-dom", async () => {
  const actual = await vi.importActual<typeof import("react-dom")>("react-dom");
  return {
    ...actual,
    createPortal: (node: ReactNode) => node,
  };
});

vi.mock("../components/integrations/GoogleSearchConsolePropertyModal", () => ({
  GoogleSearchConsolePropertyModal: ({
    open,
    selectedSiteUrl,
  }: {
    open: boolean;
    selectedSiteUrl?: string | null;
  }) =>
    open ? (
      <div data-testid="gsc-property-modal" data-selected={selectedSiteUrl ?? ""}>
        modal-open
      </div>
    ) : null,
}));

vi.mock("../components/integrations/GoogleAnalyticsPropertyModal", () => ({
  GoogleAnalyticsPropertyModal: ({
    open,
    selectedPropertyId,
  }: {
    open: boolean;
    selectedPropertyId?: string | null;
  }) =>
    open ? (
      <div data-testid="ga4-property-modal" data-selected={selectedPropertyId ?? ""}>
        modal-open
      </div>
    ) : null,
}));

vi.mock("../hooks/useProjects", () => ({
  useProject: useProjectMock,
  useProjectIntegrations: useProjectIntegrationsMock,
}));

vi.mock("../hooks/useGoogleIntegrations", () => ({
  useGoogleIntegrationStatus: useGoogleIntegrationStatusMock,
  useStartGoogleOAuth: useStartGoogleOAuthMock,
  useSearchConsoleSites: useSearchConsoleSitesMock,
  useSelectSearchConsoleSite: useSelectSearchConsoleSiteMock,
}));

vi.mock("../components/IntegrationGraph", () => ({
  IntegrationGraph: ({
    googleStatus,
  }: {
    googleStatus?: { searchConsole: { status: string }; analytics: { status: string } };
  }) => (
    <div
      data-testid="integration-graph"
      data-gsc={googleStatus?.searchConsole.status}
      data-ga4={googleStatus?.analytics.status}
    />
  ),
}));

const googleStatus = {
  pagespeed: { status: "connected", configured: true },
  crux: { status: "connected", configured: true },
  oauth: { status: "connected", configured: true },
  searchConsole: { status: "needs_setup", configured: true },
  analytics: { status: "needs_setup", configured: true },
  googleAds: {
    status: "setup_incomplete",
    configured: true,
    message: "Developer Token Google Ads mancante.",
  },
};

function countOccurrences(value: string, needle: string): number {
  return value.split(needle).length - 1;
}

function setupMocks(options?: {
  shopifyStatus?: "connected" | "not_connected";
  searchConsoleSiteUrl?: string | null;
  googleAnalyticsPropertyId?: string | null;
  googleAnalyticsPropertyName?: string | null;
}) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: {
      id: "proj-1",
      name: "Solmielato",
      searchConsoleSiteUrl: options?.searchConsoleSiteUrl ?? null,
      googleAnalyticsPropertyId: options?.googleAnalyticsPropertyId ?? null,
      googleAnalyticsPropertyName: options?.googleAnalyticsPropertyName ?? null,
    },
    isLoading: false,
  });
  useProjectIntegrationsMock.mockReturnValue({
    data: [
      {
        id: "int-1",
        projectId: "proj-1",
        provider: "shopify",
        status: options?.shopifyStatus ?? "connected",
      },
    ],
    isLoading: false,
    error: null,
  });
  useGoogleIntegrationStatusMock.mockReturnValue({
    data: googleStatus,
    isLoading: false,
  });
  useStartGoogleOAuthMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });
  useSearchConsoleSitesMock.mockReturnValue({
    data: { sites: [{ siteUrl: "https://solmielato.it/", permissionLevel: "siteOwner" }] },
    isLoading: false,
    isError: false,
  });
  useSelectSearchConsoleSiteMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });
}

function renderPage() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <IntegrationsPage />
    </MemoryRouter>,
  );
}

describe("IntegrationsPage unified grid", () => {
  it("does not render the Google Data Sources section", () => {
    setupMocks();
    const html = renderPage();
    expect(html).not.toContain("Google Data Sources");
  });

  it("renders each Google provider only once in the main grid", () => {
    setupMocks();
    const html = renderPage();

    expect(countOccurrences(html, "Google Search Console")).toBe(1);
    expect(countOccurrences(html, "Google Analytics 4")).toBe(1);
    expect(countOccurrences(html, "Google Ads")).toBe(1);
  });

  it("renders PageSpeed and CrUX in the main grid as configured", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("PageSpeed Insights");
    expect(html).toContain("Chrome UX Report");
    expect(countOccurrences(html, "Configurata")).toBeGreaterThanOrEqual(2);
  });

  it("shows Collega Google for Search Console needs_setup", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("Da collegare");
    expect(html).toContain("Collega Google");
  });

  it("shows developer token missing for Google Ads setup_incomplete", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("Developer Token mancante");
    expect(html).toContain("Setup incompleto");
    expect(html).toContain("GOOGLE_ADS_DEVELOPER_TOKEN");
  });

  it("shows Gestisci when Shopify is connected", () => {
    setupMocks({ shopifyStatus: "connected" });
    const html = renderPage();
    expect(html).toContain("Gestisci");
  });

  it("shows Connetti when Shopify is not connected", () => {
    setupMocks({ shopifyStatus: "not_connected" });
    const html = renderPage();
    expect(html).toContain("Connetti");
  });

  it("does not render inline property panel under Search Console card", () => {
    setupMocks();
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).not.toContain("gsc-property-panel");
    expect(html).not.toContain("<select");
  });

  it("shows Seleziona proprietà on connected Search Console without saved property", () => {
    setupMocks();
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).toContain("Collegata");
    expect(html).toContain("Seleziona proprietà");
    expect(html).not.toContain("Modifica proprietà");
  });

  it("shows property detail and Modifica proprietà when property is saved", () => {
    setupMocks({ searchConsoleSiteUrl: "https://solmielato.it/" });
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).toContain("Proprietà: https://solmielato.it/");
    expect(html).toContain("Modifica proprietà");
    expect(html).not.toContain("Seleziona proprietà");
  });

  it("shows Seleziona proprietà on connected GA4 without saved property", () => {
    setupMocks();
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        analytics: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).toContain("Collegata");
    expect(html).toContain("Seleziona proprietà");
    expect(html).not.toContain("ga4-property-panel");
    expect(html).not.toContain("<select");
  });

  it("shows GA4 property detail and Modifica proprietà when property is saved", () => {
    setupMocks({
      googleAnalyticsPropertyId: "123456789",
      googleAnalyticsPropertyName: "Solmielato GA4",
    });
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        analytics: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).toContain("Proprietà: Solmielato GA4");
    expect(html).toContain("Modifica proprietà");
  });

  it("passes googleStatus to Integration Graph and updates copy", () => {
    setupMocks();
    useGoogleIntegrationStatusMock.mockReturnValue({
      data: {
        ...googleStatus,
        searchConsole: { status: "connected", configured: true },
        analytics: { status: "connected", configured: true },
      },
      isLoading: false,
    });
    const html = renderPage();

    expect(html).toContain("Vista relazionale delle fonti dati collegate al progetto.");
    expect(html).not.toContain("Shopify è il primo provider attivo.");
    expect(html).toContain('data-gsc="connected"');
    expect(html).toContain('data-ga4="connected"');
  });

  it("renders brand SVG icons in the unified grid", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("integration-card__brand-icon");
    expect(html).toContain("<img");
    expect(html).toContain("Klaviyo");
  });
});
