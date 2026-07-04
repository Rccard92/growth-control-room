import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditFinding, GrowthAuditPage } from "@gcr/shared";
import {
  GrowthAuditPageDrawer,
  handleDrawerEscapeKey,
} from "./GrowthAuditPageDrawer";

const { useProductSeoDetailMock, useCollectionSeoDetailMock, useProductsSeoMock, useCollectionsSeoMock } =
  vi.hoisted(() => ({
    useProductSeoDetailMock: vi.fn(),
    useCollectionSeoDetailMock: vi.fn(),
    useProductsSeoMock: vi.fn(),
    useCollectionsSeoMock: vi.fn(),
  }));

const {
  useGrowthAuditPageResultsMock,
  useAnalyzeGrowthAuditPageWithAiMock,
} = vi.hoisted(() => ({
  useGrowthAuditPageResultsMock: vi.fn(),
  useAnalyzeGrowthAuditPageWithAiMock: vi.fn(),
}));

vi.mock("../../hooks/useContentSeo", () => ({
  useProductSeoDetail: useProductSeoDetailMock,
  useCollectionSeoDetail: useCollectionSeoDetailMock,
  useProductsSeo: useProductsSeoMock,
  useCollectionsSeo: useCollectionsSeoMock,
}));

vi.mock("../../hooks/useGrowthAudit", () => ({
  useGrowthAuditPageResults: useGrowthAuditPageResultsMock,
  useAnalyzeGrowthAuditPageWithAi: useAnalyzeGrowthAuditPageWithAiMock,
}));

function setupSeoDetailMocks() {
  const idleQuery = {
    data: undefined,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  };
  useProductSeoDetailMock.mockReturnValue(idleQuery);
  useCollectionSeoDetailMock.mockReturnValue(idleQuery);
  useProductsSeoMock.mockReturnValue(idleQuery);
  useCollectionsSeoMock.mockReturnValue(idleQuery);
  useGrowthAuditPageResultsMock.mockReturnValue({
    data: [],
    isLoading: false,
  });
  useAnalyzeGrowthAuditPageWithAiMock.mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  });
}

const samplePage: GrowthAuditPage = {
  id: "page-1",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  title: "Miele di Limone",
  metaDescription: "Miele biologico siciliano dal gusto delicato.",
  canonicalUrl: "https://solmielato.it/products/miele",
  h1: "Miele di Limone",
  httpStatus: 200,
  score: 82,
  metadata: {
    technical: {
      schemaTypes: ["Product", "WebPage"],
      imagesTotal: 5,
      imagesMissingAlt: 1,
      linksInternal: 12,
      linksExternal: 2,
      robots: { noindex: false, nofollow: false },
    },
  },
};

const sampleFinding: GrowthAuditFinding = {
  id: "finding-1",
  runId: "run-1",
  projectId: "proj-1",
  pageId: "page-1",
  category: "seo",
  severity: "critical",
  priority: "high",
  title: "Title troppo corto",
  recommendation: "Estendi il title con keyword e brand.",
  status: "open",
};

const rescanProps = {
  projectId: "proj-1",
  runId: "run-1",
  runStatus: "completed",
  onRescan: vi.fn().mockResolvedValue(undefined),
};

function countDrawerTabs(html: string): number {
  const tablist = html.split('aria-label="Sezioni dettaglio pagina"')[1] ?? "";
  const tabSection = tablist.split("growth-audit-page-drawer__tab-panels")[0] ?? "";
  return (tabSection.match(/role="tab"/g) ?? []).length;
}

describe("handleDrawerEscapeKey", () => {
  it("calls onClose when Escape is pressed", () => {
    const onClose = vi.fn();
    handleDrawerEscapeKey({ key: "Escape" } as KeyboardEvent, onClose);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("does not call onClose for other keys", () => {
    const onClose = vi.fn();
    handleDrawerEscapeKey({ key: "Enter" } as KeyboardEvent, onClose);
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe("GrowthAuditPageDrawer", () => {
  it("renders role dialog and aria-modal", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
  });

  it("renders URL, score, page type, tab bar and Chiudi button", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("https://solmielato.it/products/miele");
    expect(html).toContain("82");
    expect(html).toContain("Buona");
    expect(html).toContain("Prodotto");
    expect(html).toContain("Chiudi");
    expect(html).toContain('aria-label="Chiudi"');
    expect(html).toContain("Overview");
    expect(html).toContain("Miglioramenti");
    expect(html).toContain("Problemi");
    expect(html).toContain("Task");
    expect(html).toContain("Dati tecnici");
    expect(html).toContain("AI/GEO/CRO");
  });

  it("renders overview riepilogo and enabled rescan button when run is completed", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Riepilogo");
    expect(html).toContain("Score tecnico 82");
    expect(html).toContain("Riscansiona pagina");
    expect(html).not.toContain("disabled");
    expect(html).toContain(
      "Usalo dopo aver corretto title, meta, immagini, schema o altri elementi tecnici.",
    );
  });

  it("shows Riprova scansione label for failed pages", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{ ...samplePage, status: "failed", errorMessage: "Timeout" }}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Riprova scansione");
    expect(html).toContain("Timeout");
  });

  it("disables rescan while run is active", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        runStatus="analyzing"
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("disabled");
  });

  it("shows loading label when isRescanning", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        isRescanning
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Riscansione in corso…");
    expect(html).toContain("disabled");
  });

  it("renders overview empty Shopify state when not linked", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Nessuna entità Shopify collegata");
    expect(countDrawerTabs(html)).toBe(6);
  });

  it("renders linked Shopify entity card and Modifica Shopify tab for editable product", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{
          ...samplePage,
          sourceEntityType: "shopify_product",
          sourceEntityId: "prod-shopify-1",
          sourceEntityTitle: "Miele Premium Shopify",
          sourceEntityHandle: "miele",
        }}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Entità Shopify collegata");
    expect(html).toContain("Prodotto Shopify");
    expect(html).toContain("Miele Premium Shopify");
    expect(html).toContain("miele");
    expect(html).toContain("Modifica Shopify");
    expect(html).toContain("Usa la tab Modifica Shopify");
    expect(html).not.toContain("Nel prossimo step potrai modificare title");
    expect(countDrawerTabs(html)).toBe(7);
  });

  it("does not show Modifica Shopify tab without sourceEntityId", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{
          ...samplePage,
          sourceEntityType: "shopify_product",
          sourceEntityTitle: "Miele",
          sourceEntityHandle: "miele",
        }}
        findings={[sampleFinding]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(countDrawerTabs(html)).toBe(6);
  });

  it("does not show Modifica Shopify tab without sourceEntityId", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{
          ...samplePage,
          sourceEntityType: "shopify_page",
          sourceEntityTitle: "Chi siamo",
          sourceEntityHandle: "chi-siamo",
        }}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Pagina Shopify");
    expect(html).toContain("Modifica Shopify per pagine e articoli in arrivo.");
    expect(countDrawerTabs(html)).toBe(6);
  });

  it("hides AI tab when page is not analyzed", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{ ...samplePage, status: "failed" }}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).not.toContain("AI/GEO/CRO");
    expect(countDrawerTabs(html)).toBe(5);
  });

  it("returns null when closed", () => {
    setupSeoDetailMocks();
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open={false}
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toBe("");
  });
});
