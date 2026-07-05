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

function setupMocks() {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
    isLoading: false,
  });
  useProjectIntegrationsMock.mockReturnValue({
    data: [{ id: "int-1", projectId: "proj-1", provider: "shopify", status: "connected" }],
    isLoading: false,
    error: null,
  });
  useGoogleIntegrationStatusMock.mockReturnValue({
    data: {
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
    },
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

describe("IntegrationsPage Google section", () => {
  it("shows Google Data Sources section with PageSpeed and CrUX configured", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Google Data Sources");
    expect(html).toContain("PageSpeed Insights");
    expect(html).toContain("Chrome UX Report");
    expect(html).toContain("Configurata");
  });

  it("shows Search Console needs setup and Collega Google CTA", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Search Console");
    expect(html).toContain("Da collegare");
    expect(html).toContain("Collega Google");
  });

  it("shows Google Ads developer token missing note", () => {
    setupMocks();
    const html = renderPage();
    expect(html).toContain("Google Ads");
    expect(html).toContain("Developer Token mancante");
    expect(html).toContain("Setup incompleto");
  });
});
