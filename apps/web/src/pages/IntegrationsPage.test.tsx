import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { IntegrationsPage } from "./IntegrationsPage";

const {
  useParamsMock,
  useProjectMock,
  useProjectIntegrationsMock,
  useGoogleIntegrationStatusMock,
  useStartGoogleOAuthMock,
} = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useProjectIntegrationsMock: vi.fn(),
  useGoogleIntegrationStatusMock: vi.fn(),
  useStartGoogleOAuthMock: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: useParamsMock,
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

vi.mock("../hooks/useProjects", () => ({
  useProject: useProjectMock,
  useProjectIntegrations: useProjectIntegrationsMock,
}));

vi.mock("../hooks/useGoogleIntegrations", () => ({
  useGoogleIntegrationStatus: useGoogleIntegrationStatusMock,
  useStartGoogleOAuth: useStartGoogleOAuthMock,
}));

vi.mock("../components/IntegrationGraph", () => ({
  IntegrationGraph: () => null,
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

function setupMocks(options?: { shopifyStatus?: "connected" | "not_connected" }) {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
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

  it("renders brand SVG icons in the unified grid", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("integration-card__brand-icon");
    expect(html).toContain("<img");
    expect(html).toContain("Klaviyo");
  });
});
