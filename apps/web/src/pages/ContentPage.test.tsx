import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { ContentPage } from "./ContentPage";

const { useParamsMock, useProjectMock, useShopifyStatusMock } = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  useProjectMock: vi.fn(),
  useShopifyStatusMock: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useParams: useParamsMock,
  };
});

vi.mock("../hooks/useProjects", () => ({
  useProject: useProjectMock,
}));

vi.mock("../hooks/useShopify", () => ({
  useShopifyStatus: useShopifyStatusMock,
}));

vi.mock("../components/content/editorial/ContentSeoEditorialRoom", () => ({
  ContentSeoEditorialRoom: () => (
    <div className="editorial-room">
      <h2 className="editorial-room__title">Calendario editoriale</h2>
    </div>
  ),
}));

function setupMocks() {
  useParamsMock.mockReturnValue({ id: "proj-1" });
  useProjectMock.mockReturnValue({
    data: { id: "proj-1", name: "Solmielato" },
    isLoading: false,
  });
  useShopifyStatusMock.mockReturnValue({
    data: { connected: true, shopDomain: "solmielato.myshopify.com" },
  });
}

function renderPage() {
  return renderToStaticMarkup(
    <MemoryRouter>
      <ContentPage />
    </MemoryRouter>,
  );
}

describe("ContentPage", () => {
  it("renders Content SEO title and editorial room", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("Content SEO");
    expect(html).toContain("Calendario editoriale");
    expect(html).toContain("editorial-room");
  });

  it("does not render products tab or SeoOptimizerRoom", () => {
    setupMocks();
    const html = renderPage();

    expect(html).not.toContain("Prodotti &amp; Categorie");
    expect(html).not.toContain("Prodotti & Categorie");
    expect(html).not.toContain("content-seo-tabs");
    expect(html).not.toContain("seo-optimizer-tabs");
  });

  it("shows Growth Audit redirect card and CTA link", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("Prodotti e categorie si ottimizzano in Growth Audit");
    expect(html).toContain("Apri Growth Audit");
    expect(html).toContain('href="/projects/proj-1/audit"');
  });

  it("shows updated subtitle pointing to Growth Audit for products", () => {
    setupMocks();
    const html = renderPage();

    expect(html).toContain("ottimizzazione di prodotti e categorie Shopify ora vive in Growth Audit");
  });
});
